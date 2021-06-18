from grbl_comm import GrblComm

comm = GrblComm()

status = comm.get_status()
print(status)

gcode_list = ['F400.0', 'G0 X10']
comm.send_gcode(gcode_list, verbose=True)

print(comm.get_status())


#print()
#comm.print_settings()
#
#print()
#status = comm.get_status()
#print(status)
#
#
#print()
#status = comm.get_status()
#print(status)


#print()
#comm.print_help()
#
#params = comm.get_gcode_parameters()
#print()
#for item in params:
#    print(item)
#
#pstate = comm.get_parser_state()
#print()
#print(pstate)
#
#status = comm.get_status()
#print()
#print(status)
#
#info = comm.get_build_info()
#print()
#print(info)
#
#comm.reset()
#print()
#
#print()
#comm.print_help()
#print()


#comm.print_sys_cmd()
#print()
#
#comm.set_x_step_per_mm(250.0)
#comm.print_settings()







