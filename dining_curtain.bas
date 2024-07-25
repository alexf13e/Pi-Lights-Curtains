#simspeed 10
#picaxe 18m2

' dining curtains controller : controlled solely by main controller rf link
'pin i/o function
'1  pwr +ve +5v 
'2  i/p c.5 serial data in (for programming)
'3  i/p c.4 inhibit operation if doors open
'4  i/p c.3 incoming pulses from RF receiver
'5  o/p c.2 to curtain motor
'6  i/p c.1 current trip from motor
'7  o/p serial out // direction relay out 
'8  0V 


'variables
'w0 =  (b0, b1)	used
'w1 =  (b2, b3)	used
'w2 =  (b4, b5)	used
'w3 =  (b6, b7) 	used
'w4 =  (b8, b9)
'w5 =  (b10,b11)
'w6 =  (b12,b13)
'w7 =  (b14,b15)
'w8 =  (b16,b17)
'w9 =  (b18,b19)
'w9 =  (b20,b21)
'w10 = (b22,b23)	motor run time
'w11 = (b24,b25)	motor current level 2
'w12 = (b16,b17)	motor current level 1
'w13 = (b26,b27)	motor current level 0
'b0 = (w0)		curtain state
'b1 = (w0)		door delay
'b2 = (w1)		shaft state old
'b3 = (w1)		shaft state new
'b4 = (w2)		shaft pulse count
'b5 = (w2)		curtains waiting to close when next possible
'b6 = (w3)		curtains waiting to open when next possible
'b7 = (w3)
'b8 = (w4)
'b9 = (w4)
'b10 = (w5)
'b11 = (w5)
'b12 = (w6)
'b13 = (w6)
'b14 = (w7)
'b15 = (w7)
'b16 = (w8)
'b17 = (w8)
'b18 = (w9)
'b19 = (w9)
'b20 = (w10)	used
'b21 = (w10)	used
'b22 = (w11)	used
'b23 = (w11)	used
'b24 = (w12)	used
'b25 = (w12)	used
'b26 = (w13)	used
'b27 = (w13)	used


'************************************************** This part only runs once, when powered up**********************************************
						'
						'
pause 2000					'
						'
symbol in_door_inhibit = pinC.2	' hi = doors open
symbol in_signal_0 = pinB.0		'
symbol in_signal_1 = pinB.1		'
symbol in_signal_2 = pinB.2		'
symbol in_signal_3 = pinB.3		'
symbol out_opto_power = B.4		'
symbol in_shaft_value = pinB.5	' 
symbol in_motor_current = C.1		' analogue read of motor current
symbol out_motor_direction = C.0	' hi = open
symbol out_motor_power = B.7		' hi = run motor
						'
						'
symbol motor_max_time = 900		' 9 sec max motor run time (used only as safeguard) - measured in number of loops in motor sub, unknown exactly how long
symbol motor_trip_threshold = 100	' value at which motor_current will cause the motor to stop running
symbol shaft_count_threshold = 145	'
symbol motor_current_level_0 = w13	' location for reading in data from in_motor_current
symbol motor_current_level_1 = w12	' previous current reading to level_0
symbol motor_current_level_2 = w11	' previous current reading to level_1
symbol motor_run_time = w10		'
symbol curtain_state = b0		' 1 = open, 0 = closed
symbol door_delay = b1			'
symbol shaft_state_new = b2		'
symbol shaft_state_old = b3		'
symbol shaft_pulse_count = b4		'
symbol awaiting_close = b5		' curtains want to close when next possible
symbol awaiting_open = b6		' curtains want to open when next possible
						'
motor_current_level_0 = 0		'
motor_current_level_1 = 0		'
motor_current_level_2 = 0		'
motor_run_time = 0			'
curtain_state = 0				' doesn't know the actual state of the curtain, but worst case it tries to open when already open, the current trip stops is and now it matches the actual state
door_delay = 0				'
shaft_state_new = 0			'
shaft_state_old = 0			'
shaft_pulse_count = 0			'
awaiting_close = 0			'
awaiting_open = 0				'
						'
						'
						'
						'
'************************************************** This part only runs once, when powered up**********************************************




main:
	' check input signals. 0100 = close, 0101 = open
	if in_signal_0 = 0 and in_signal_1 = 1 and in_signal_2 = 0 then
		' signal is for the dining curtains, check if being told to open or close
		;sertxd("received signal for curtains: ", in_signal_0, in_signal_1, in_signal_2, in_signal_3, cr, lf)
		if in_signal_3 = 0 then
			;sertxd("asking to close", cr, lf)
			awaiting_close = 1
			awaiting_open = 0
		end if
	
		if in_signal_3 = 1 then
			;sertxd("asking to open", cr, lf)
			awaiting_close = 0
			awaiting_open = 1
		end if
	endif

	' inhibit operation when doors open (relay operated by door open switch)
	if in_door_inhibit = 1 then
		door_delay = 1	' if the door is open remember the fact
	else
		' door is shut
		if awaiting_close = 1 then
			awaiting_close = 0
			if curtain_state = 1 then
				gosub close
				curtain_state = 0
			end if
		end if
	
		if awaiting_open = 1 then
			awaiting_open = 0
			if curtain_state = 0 then
				gosub open
				curtain_state = 1
			end if
		end if
		
		door_delay = 0	' door is closed so clear the flag - need to run through close before changing this to 0 so there is a 30 second delay between the door shutting and the curtains closing
	endif
goto main
end


close:
	if door_delay = 1 then
		pause 30000 ' 30 second deay if the door WAS open previously
	endif

	gosub motor		' run motor with out_motor_direction low to close
return
		
open:
	high out_motor_direction
	pause 250
	gosub motor
	low out_motor_direction	
return

motor:
	high out_opto_power
	high out_motor_power ' start curtain motor
	;resume 1	' resume thread to monitor current at same time
	
	pause 500	' wait for initial current to drop
	
	shaft_pulse_count = 0		' reset pulse count to 0
	motor_current_level_0 = 0	' reset previous current readings
	motor_current_level_1 = 0
	motor_current_level_2 = 0
	
	for motor_run_time = 0 to motor_max_time ' loop for time period (safeguard only to stop motor after max motor run time (9 sec))
		
		if in_signal_0 = 0 and in_signal_1 = 1 and in_signal_2 = 0 and in_signal_3 = curtain_state then	' the input is saying to close and we were in the process of opening, or other way round
			;sertxd("interrupted, asking to change direction: ", in_signal_0, in_signal_1, in_signal_2, in_signal_3, cr, lf)
			;sertxd("curtain state: ", curtain_state, cr, lf)
			curtain_state = 1 - curtain_state
			gosub motor_stop
			goto main
		end if
		
		shaft_state_new = in_shaft_value
		if shaft_state_new = 1 and shaft_state_old = 0 then
			shaft_pulse_count = shaft_pulse_count + 1
		endif
		shaft_state_old = shaft_state_new
		
		if shaft_pulse_count >= shaft_count_threshold then
			gosub motor_stop
			return
		end if
		
		motor_current_level_2 = motor_current_level_1	' move the previous readings along, oldest in level_2
		motor_current_level_1 = motor_current_level_0
		readadc in_motor_current, motor_current_level_0
		if motor_current_level_0 >= motor_trip_threshold and motor_current_level_1 >= motor_trip_threshold and motor_current_level_2 >= motor_trip_threshold then
			;sertxd("motor current trip: ", motor_current_level_0, cr, lf)
			gosub motor_stop
			return
		endif
	
	next motor_run_time ' safeguard only to stop motor after max motor run time (9 sec) - motor will normally current trip)

	;sertxd("stopping motor from time", cr, lf)

motor_stop:
	low out_motor_power
	low out_opto_power
	pause 250
	low out_motor_direction
	;sertxd("motor stopped", cr, lf)
	;sertxd("pulse count: ", shaft_pulse_count, cr, lf)
	;sertxd("time: ", motor_run_time, cr, lf)
return

;#terminal 4800	' opens terminal window after download