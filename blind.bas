#simspeed 10
#picaxe 08m2

' lounge blind controller : controlled solely by main controller rf link
' Blind operation and stop position is controlled within blind motor control unit....all it needs is polarity reversal
'pin i/o function
'1  pwr V+ 
'2  i/p c.4 serial data in (for programming)
'3  c.4
'4  c.3 
'5  c.2 out to relay 
'6  in from RF600D pin 1 (channel 3)
'7  c.0 serial data out (for programming)
'8  pwr 0V

'variables
'w0 =  (b0,b1)
'w1 =  (b2,b3)
'w2 =  (b4,b5)
'w3 =  (b6,b7) 
'w4 =  (b8,b9)
'w5 =  (b10,b11) 
'w6 =  (b12,b13)
'w7 =  (b14,b15)
'w8 =  (b16,b17)
'w9 =  (b18,b19)
'w9 =  (b20,b21)
'w10 = (b22,b23)
'w11 = (b24,b25)
'w12 = (b16,b17)
'w13 = (b26,b27)
'b0 =  (w0)
'b1 =  (w0)
'b2 = (w1)
'b3 = (w1)
'b4 = (w2)
'b5 = (w2)
'b6 = (w3)
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
'b20 = (w10) 
'b21 = (w10) 
'b22 = (w11) 
'b23 = (w11) 
'b24 = (w12) 
'b25 = (w12)
'b26 = (w13)
'b27 = (w13)

'************************************************** This part only runs once, when powered up**********************************************
							'																*
setfreq mdefault					' sertxd command syntax = e.g. ("main  ",#ldr, cr,lf)		

symbol out_relay = C.0

symbol in_signal_0 = pinC.1
symbol in_signal_1 = pinC.2
symbol in_signal_2 = pinC.3
symbol in_signal_3 = pinC.4

pause 2000	; allow time after powering up to reprogram before reaching disconnect

disconnect

'************************************************** This part only runs once, when powered up**********************************************

main: 
	if in_signal_0 = 0 and in_signal_1 = 0 and in_signal_2 = 1 then
		' signal is for the lounge blind, check if being told to open or close
		;sertxd("received signal for blind: ", in_signal_0, in_signal_1, in_signal_2, in_signal_3, cr, lf)
		if in_signal_3 = 0 then
			;sertxd("asking to close", cr, lf)
			gosub close
		end if
		if in_signal_3 = 1 then
			;sertxd("asking to open", cr, lf)
			gosub open
		end if
	endif
goto main
end


close:
	;sertxd (#w1, " pulses = blind close [105] ", cr,lf)
	high out_relay			' operates relay, blind closes
	pause 1000
	return
		
open:
	;sertxd (#w1, " pulses = blind open [110] ", cr,lf)
	low out_relay			' releases relay, blind opens
	pause 1000
	return

'#terminal 4800		' opens terminal window after download