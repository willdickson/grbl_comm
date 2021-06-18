from __future__ import print_function
import time
import serial


# Utility
# -----------------------------------------------------------------------------

def dummy_send_converter(value):
    return value

def bool_send_converter(value):
    return int(value)

# -----------------------------------------------------------------------------


class GrblComm(serial.Serial):

    RESET_DT = 2.0
    IDLE_POLL_DT = 0.25
    RX_BUFFER_SIZE = 128
    CMD_HELP = '$'
    CMD_GET_STATUS = '?'
    CMD_GET_SETTINGS = '$$'
    CMD_GET_GCODE_PARAM = '$#'
    CMD_GET_PARSER_STATE = '$G'
    CMD_GET_BUILD_INFO = '$I'
    CMD_RESET_GRBL = '\x18' 

    SYS_CMD_DICT = {
            'step_pulse_usec'          : '$0',
            'step_idle_delay_msec'     : '$1',
            'step_port_invert_mask'    : '$2',
            'dir_port_invert_mask'     : '$3',
            'step_enable_invert'       : '$4',
            'limit_pins_invert'        : '$5',
            'probe_pin_invert'         : '$6',
            'status_report_mask'       : '$10',
            'junction_deviation_mm'    : '$11',
            'arc_tolerance_mm'         : '$12',
            'report_inches'            : '$13',
            'soft_limits'              : '$20',
            'hard_limits'              : '$21',
            'homing_cycle'             : '$22',
            'homing_dir_invert_mask'   : '$23',
            'homing_feed_mm_per_min'   : '$24',
            'homing_seek_mm_per_min'   : '$25',
            'homing_debounce_msec'     : '$26',
            'homing_pull_off_mm'       : '$27',
            'x_step_per_mm'            : '$100',
            'y_step_per_mm'            : '$101',
            'z_step_per_mm'            : '$102',
            'x_max_rate_mm_per_min'    : '$110',
            'y_max_rate_mm_per_min'    : '$111',
            'z_max_rate_mm_per_min'    : '$112',
            'x_accel_mm_per_sec2'      : '$120',
            'y_accel_mm_per_sec2'      : '$121',
            'z_accel_mm_per_sec2'      : '$122',
            'x_max_travel_mm'          : '$130',
            'y_max_travel_mm'          : '$131',
            'z_max_travel_mm'          : '$132',
            }

    SYS_CMD_TYPE_DICT = {
            'step_pulse_usec'          : int,
            'step_idle_delay_msec'     : int,
            'step_port_invert_mask'    : int,
            'dir_port_invert_mask'     : int,
            'step_enable_invert'       : bool,
            'limit_pins_invert'        : bool,
            'probe_pin_invert'         : bool,
            'status_report_mask'       : int,
            'junction_deviation_mm'    : float,
            'arc_tolerance_mm'         : float,
            'report_inches'            : bool,
            'soft_limits'              : bool,
            'hard_limits'              : bool,
            'homing_cycle'             : bool,
            'homing_dir_invert_mask'   : int,
            'homing_feed_mm_per_min'   : float,

            'homing_seek_mm_per_min'   : float,
            'homing_debounce_msec'     : int,
            'homing_pull_off_mm'       : float,
            'x_step_per_mm'            : float,
            'y_step_per_mm'            : float,
            'z_step_per_mm'            : float,
            'x_max_rate_mm_per_min'    : float,
            'y_max_rate_mm_per_min'    : float,
            'z_max_rate_mm_per_min'    : float,
            'x_accel_mm_per_sec2'      : float,
            'y_accel_mm_per_sec2'      : float,
            'z_accel_mm_per_sec2'      : float,
            'x_max_travel_mm'          : float,
            'y_max_travel_mm'          : float,
            'z_max_travel_mm'          : float,
            }


    SYS_CMD_VALUE_CONVERTERS = {
            int   : dummy_send_converter,
            float : dummy_send_converter,
            bool  : bool_send_converter, 
            }


    def __init__(self, port='/dev/ttyACM0', baudrate=115200, timeout=None):
        super().__init__(port, baudrate=baudrate, timeout=timeout)
        self.wakeup()
        time.sleep(self.RESET_DT)
        self.flushInput()
        self.add_sys_cmd_methods()

    def add_sys_cmd_methods(self):
        for cmd_name in self.SYS_CMD_DICT:
            setattr(GrblComm, 'get_{}'.format(cmd_name), self.make_sys_cmd_getter(cmd_name))
            setattr(GrblComm, 'set_{}'.format(cmd_name), self.make_sys_cmd_setter(cmd_name))

    def make_sys_cmd_getter(self, name):
        def sys_cmd_getter(self):
            settings_dict = self.get_settings()
            return settings_dict[name]
        return sys_cmd_getter 

    def make_sys_cmd_setter(self, name):
        value_type = self.SYS_CMD_TYPE_DICT[name]
        def sys_cmd_setter(self, value):
            converted_value = self.SYS_CMD_VALUE_CONVERTERS[value_type](value)
            cmd = '{0}={1}\n'.format(self.SYS_CMD_DICT[name], converted_value)
            rsp_lines = self.send_cmd(cmd)
            self.flushInput() # not sure why this is required ... extra stuff comming back??
        return sys_cmd_setter

    def wakeup(self):
        self.write('\n\r\n\r'.encode())

    def get_status(self):
        cmd = self.CMD_GET_STATUS
        self.write(cmd.encode()) 
        line = self.readline()
        line = line.strip()
        line = line.decode('UTF-8')
        line_list = line[1:-1].replace(':',',').split(',')
        status = {'mode': line_list[0].lower()} 
        pos = 1
        while pos < len(line_list):
            if line_list[pos] in ('MPos','WPos'):
                k = line_list[pos]
                x = float(line_list[pos+1])
                y = float(line_list[pos+2])
                z = float(line_list[pos+3])
                status[k] = {'x': x, 'y': y, 'z': z}
                pos += 4
        return status 

    def reset(self):
        cmd = self.CMD_RESET_GRBL
        self.write(cmd.encode())
        time.sleep(self.RESET_DT)
        line = self.readline()
        return line

    def get_settings(self):
        cmd = self.CMD_GET_SETTINGS
        line_list = self.send_cmd(cmd)
        settings_dict = {}
        for cmd_key, cmd_val in self.SYS_CMD_DICT.items():
            for line in line_list:
                if '{}='.format(cmd_val) in line:
                    val_str = line.split()[0]
                    val_pos = val_str.find('=')+1
                    val_str = val_str[val_pos:]
                    settings_dict[cmd_key] = self.SYS_CMD_TYPE_DICT[cmd_key](val_str) 
        return settings_dict

    def get_gcode_parameters(self):
        cmd = self.CMD_GET_GCODE_PARAM
        rsp_lines = self.send_cmd(cmd)
        return rsp_lines

    def get_parser_state(self):
        cmd = self.CMD_GET_PARSER_STATE
        rsp_lines = self.send_cmd(cmd)
        return rsp_lines[0]

    def get_build_info(self):
        cmd = self.CMD_GET_BUILD_INFO
        rsp_lines = self.send_cmd(cmd)
        return rsp_lines[0]

    def get_list_of_sys_cmd(self):
        sys_cmd = []
        sys_cmd.extend(['get_{}'.format(k) for k in self.SYS_CMD_DICT])
        sys_cmd.extend(['set_{}'.format(k) for k in self.SYS_CMD_DICT])
        return sys_cmd

    def print_sys_cmd(self):
        sys_cmd = self.get_list_of_sys_cmd()
        for k in sys_cmd:
            print(k)

    def print_settings(self):
        settings_dict = self.get_settings()
        for k,v in settings_dict.items():
            print('{0}: {1}'.format(k,v))

    def print_help(self):
        cmd = self.CMD_HELP 
        line_list = self.send_cmd(cmd)
        for line in line_list:
            print(line)

    def send_cmd(self,cmd):
        self.write('{}\n'.format(cmd).encode())
        ok = True
        error_msg = ''
        line_list = []
        while True:
            line = self.readline().decode('UTF-8')
            line = line.strip()
            if 'ok' in line:
                break
            if 'error' in line:
                ok = False
                error_msg = line
                break
            line_list.append(line)
        if ok:
            return line_list
        else:
            return error_msg


    def send_gcode(self, gcode_list, verbose=False):

        char_cnt_list =  []
        gcode_cnt = 0

        # Loop over buffer sending commands - monitor size ofbuffered commands 
        # to make sure that we stay with size of receive buffer. 
        for num, cmd in enumerate(gcode_list):
            char_cnt_list.append(len(cmd)+1)
            grbl_out = [] 
            while sum(char_cnt_list) >= self.RX_BUFFER_SIZE | self.in_waiting:
                rsp = self.readline().decode('UTF-8').strip()
                if rsp.find('ok') < 0 and rsp.find('error') < 0:
                    raise RuntimeError('unexpected grbl response: {}'.format(rsp))
                else:
                    gcode_cnt += 1
                    grbl_out.append('{0}: {1}'.format(rsp,gcode_cnt)) 
                    del char_cnt_list[0]
            if verbose: 
                print('SND: {0} : {1}'.format(num, cmd))
            self.write('{}\n'.format(cmd).encode())
            if verbose:
                print('BUF: {}'.format(sum(char_cnt_list)), end='')
                if grbl_out:
                    print(' REC: {}'.format(",".join(grbl_out)))
                else:
                    print()
            
        # Done sending commands
        if verbose:
            print('Gcode streaming finished ... waiting for commands to finish')

        # Receive return codes from remaining commands in buffer
        while gcode_cnt < len(gcode_list):
            rsp = self.readline().decode('UTF-8').strip()
            if rsp.find('ok') < 0 and rsp.find('error') < 0:
                raise RuntimeError('unexpected grbl response: {}'.format(rsp))
            else:
                gcode_cnt += 1
                grbl_out = '{0}: {0}'.format(rsp, gcode_cnt) 
                del char_cnt_list[0]
                if verbose:
                    print('BUF: {0} REC: {1}'.format(sum(char_cnt_list), grbl_out))

        # Wait until system returns to the idle state
        done = False
        while not done:
            status = self.get_status()
            if status['mode'] == 'idle':
                done = True
            time.sleep(self.IDLE_POLL_DT)

    
