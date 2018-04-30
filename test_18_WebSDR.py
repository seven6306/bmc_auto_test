#!/usr/bin/python3
# 9. Web UI
# 9-1. Dashboard
#      Sensor Monitoring - Verify all the sensors can be viewed.
# 9-3. Server Health - Sensor Readings
#      1.Verify sensor name, status, current reading, thresholds
#        are correct.(follow the sensor list) 
#      2.Verify all the thresholds can be configured.
#      3.Verify each "Sensor Live Widget" can work normally.
#      4.Verify the help info can display normally.

import sys
sys.path.append('./lib')
from PublicModule import *

info = """
\033[1m## Verify data key name as below listed:\033[0m
==========================================
  1. accessible (status)
  2. higher_critical_threshold
  3. higher_non_critical_threshold
  4. higher_non_recoverable_threshold
  5. lower_critical_threshold
  6. lower_non_critical_threshold
  7. lower_non_recoverable_threshold
  8. name
  9. reading
  10. type
==========================================

"""

class TestWebUserInterface(object):
    @mark.order1
    def test_sdr_info(self):
        gLogger.info('\n\n')
        gLogger.debug('\033[93m[9-3]\033[0m \033[1mVerify sensor name, status' +
                      ', current reading, thresholds are correct.\033[0m')

        total_fail_count = 0
        torlerance = 0.1
        sdr_dict = {}
        sdr_api_dict = {}
        mark1 = ' \033[94m(ipmi)\033[0m'
        mark2 = ' \033[93m(web)\033[0m'
        sensor_ls = ['name',
                     'reading',
                     'type',
                     'stat_bak',
                     'lower_non_recoverable_threshold',
                     'lower_critical_threshold',
                     'lower_non_critical_threshold',
                     'higher_non_critical_threshold',
                     'higher_critical_threshold',
                     'higher_non_recoverable_threshold']

        cmd_sdr_list = ''.join(['ipmitool -H {} -I lanplus '.format(gBmcIp),
                               '-U {} -P '.format(gUserName) +
                               '{} sdr list'.format(gPassWord)])
        cmd_sensor_list = ''.join(['ipmitool -H {} -I lanplus '.format(gBmcIp),
                               '-U {} -P '.format(gUserName) +
                               '{} sensor list'.format(gPassWord)])
        cmd_get_sdr = ''.join(['ipmitool -H {} -I lanplus '.format(gBmcIp),
                               '-U {} -P '.format(gUserName) +
                               '{} sdr get'.format(gPassWord)])

        # print verify detail
        gLogger.info(info)

        sdr_list1 = os.popen(cmd_sdr_list).read().split('\n')
        sdr_list2 = os.popen(cmd_sensor_list).read().split('\n')
        [sdr_list1.remove(e) for e in sdr_list1 if e == '']
        [sdr_list2.remove(e) for e in sdr_list2 if e == '']

        # parse data by get sdr via ipmi command
        for e in sdr_list2:
            tmp_dict = {}
            for i, tmp in enumerate(sensor_ls):
                tmp_dict[tmp] = e.split('|')[i].strip()
            sdr_dict[tmp_dict['name']] = tmp_dict
        for e in sdr_list1:
            tmp_name = e.split('|')[0].strip()
            tmp_status = e.split('|')[2].strip()
            sdr_dict[tmp_name]['accessible'] = tmp_status

        # parse data by get sdr via web api
        api = RestfulApi()
        sdr_api_list = api.GetInformation(api='sensors')
        api.Close()
        for e in sdr_api_list:
            key = e['name']
            value = e
            sdr_api_dict[key] = value

        # compare data from ipmi and web api
        for i, (k, v) in enumerate(sorted(sdr_dict.items())):
            gLogger.debug(' Device [' + k + ']')
            gLogger.debug('    ' + gTreeTrunk)
            fail_count = 0
            for kk, vv in sorted(v.items()):
                if kk not in ['stat_bak']:
                    miss = ''
                    status1 = vv
                    status2 = str(sdr_api_dict[k][kk])
                    if kk == 'accessible':
                        if sdr_api_dict[k][kk] == 0:
                            status2 = 'ok'
                        else:
                            status2 = 'ns'
                    if '_threshold' in kk and vv == 'na':
                        status1 = '0.0'

                    try:
                        # verify device name
                        if 'name' in [kk, sdr_api_dict[k]]:
                            if status1 != status2:
                                raise
                        # verify status only catch string ok
                        if status1 == 'ok' or status2 == 'ok':
                            if status1 != status2:
                                raise
                        # verify thresholds (torlerance value > 0.1)
                        if 'threshold' in kk or 'threshold' in sdr_api_dict[k]:
                            if abs(float(status1) - float(status2)) > torlerance:
                                raise
                    except:
                        miss = '\033[91m <- mis-match\033[0m'
                        fail_count += 1

                    # verify current reading must be between in minimum
                    # and maximum and each torlerance value > 0.1
                    if 'reading' in [kk, sdr_api_dict[k]]:
                        min = sdr_api_dict[k]['lower_non_critical_threshold']
                        max = sdr_api_dict[k]['higher_non_critical_threshold']
                        try:
                            for e_ft in [float(max),
                                         float(vv),
                                         float(sdr_api_dict[k][kk])]:
                                if e_ft == 0:
                                    raise
                            if abs(float(status1) - float(status2)) > torlerance:
                                raise ImportWarning
                            if float(status2) > float(max) or float(status2) < float(min):
                                raise ImportWarning
                        except ImportWarning:
                            miss = '\033[91m <- mis-match\033[0m'
                            fail_count += 1
                        except:
                            pass

                    if miss != '':
                        tree1 = gTreeBranch
                        tree2 = gTreeTrunk
                        bar = '    ' + tree2 + '   '
                        gLogger.debug('    ' + tree1 + kk + miss)
                        gLogger.debug(bar + gTreeBranch + status1 + mark1)
                        gLogger.debug(bar + gTreeRoot + status2 + mark2)

            total_fail_count += fail_count
            if fail_count == 0:
                tree1 = gTreeBranch
                tree2 = gTreeTrunk
                if i == len(sdr_dict.items()) - 1:
                    tree1 = gTreeRoot
                    tree2 = ''
                gLogger.debug('    ' + tree1 + '[\033[92mPASS\033[0m]')
                gLogger.debug('    ' + tree2)

        # verify fail occured count
        if total_fail_count != 0:
            gLogger.warning('\033[91msome sensor data is mis-match, error ' +
                            'found number: {}\033[0m'.format(total_fail_count))
            assert False, 'some sensor data is mis-match'

        gLogger.info('')
        gLogger.info('\033[1m=> All the sensor data are correct.\033[0m')
        gLogger.info('\n')
        gLogger.debug('\033[1m ***** [{}'.format(strftime('%Y-%m-%d %H:%M:%S')) +
                     '] Verify sensor name, status, current reading' +
                     ', thresholds are correct. [\033[0m' +
                     '{}\033[1m] *****\033[0m'.format(gPassGreen))
        assert True

"""
    @mark.order2
    def test_sdr_config(self):
        gLogger.info('\n\n')
        gLogger.debug('\033[93m[9-1]\033[0m \033[1mVerify all the thresholds' +
                      ' can be configured\033[0m')
        gLogger.info('')
        gLogger.info('\033[1m=> All the thresholds can be configured.\033[0m')
        gLogger.info('\n')
        gLogger.debug(
            '\033[1m ***** [{0}] Verify all the thresholds can be configured [\033[0m{1}\033[1m] *****\033[0m'.format(
                strftime('%Y-%m-%d %H:%M:%S'), gPassGreen))
        assert True
    @mark.order3
    def test_sdr_slw(self):
        gLogger.info('\n\n')
        gLogger.debug('\033[93m[9-1]\033[0m \033[1mVerify each "Sensor Live ' +
                      'Widget" can work normally.\033[0m')
        gLogger.info('')
        gLogger.info('\033[1m=> All the Sensor Live Widget can work normally.\033[0m')
        gLogger.info('\n')
        gLogger.debug(
            '\033[1m ***** [{0}] Verify each "Sensor Live Widget" can work normally. [\033[0m{1}\033[1m] *****\033[0m'.format(
                strftime('%Y-%m-%d %H:%M:%S'), gPassGreen))
        assert True
    @mark.order4
    def test_sdr_help(self):
        gLogger.info('\n\n')
        gLogger.debug('\033[93m[9-1]\033[0m \033[1mVerify the help info can ' +
                      'display normally.\033[0m')
        gLogger.info('')
        gLogger.info('\033[1m=> The help info can be displayed.\033[0m')
        gLogger.info('\n')
        gLogger.debug(
            '\033[1m ***** [{0}] Verify the help info can display normally [\033[0m{1}\033[1m] *****\033[0m'.format(
                strftime('%Y-%m-%d %H:%M:%S'), gPassGreen))
        assert True
"""