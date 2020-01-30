#!/usr/bin/python
# Copyright (C) 2019 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import numpy as np
import time
import adi

# Channel scale factors
adc_scale = 0.000149011 #Vref=2.5; adc_scale=[2.5/(2^24)]
ldoU2_temp_scale = 1.0 # Degrees C/mV
ldoU3_temp_scale = 1.0 # Degrees C/mV
iout_scale = 0.005 # A/mV
vin_scale =  14.33/1000 # V/mV; vin_scale = 1/(21.5/1.5)
vout_scale =  10.52/1000 # V/mV; vout_sca;e = 1/(22.1/2.1)
ilim_pos_scale =  100.0/(2.5*1000) # Percent
vpot_pos_scale =  100.0/(2.5*1000) # Percent

def main(my_ip):
    try:
        myadc = adi.ad7124(uri=my_ip, part="ad7124-4")
        mydac = adi.ad5683r(uri=my_ip) # REMEMBER TO VERIFY POWERDOWN/UP BEHAVIOR
    except:
      print("No device found")
      sys.exit(0)

    print("setting up DAC, setting output to 2.5V...")
    mydac.raw = '11000'#'5958' # Hardcoded value, dependent on CN0508 op-amp gain
    dac_scale = mydac.scale # This is set by the device tree, it's not an actual measured value.
    print("DAC scale factor: " + str(dac_scale))

    print("Setting sample rates...")
    #Set maximum sampling frequency
    myadc.sample_rate = 9600

    print("Setting scales to 0.000149011 (unity gain)...")
    for i in range(0, 8):
      myadc.channel[i].scale = adc_scale

    print("Reading all voltages...\n\n")

    # Calculate parameters
    # (Copy and paste below as needed...)
    ldoU2_temp = (float(myadc.channel[0].raw) * adc_scale) * ldoU2_temp_scale
    ldoU3_temp = (float(myadc.channel[1].raw) * adc_scale) * ldoU3_temp_scale
    iout = (float(myadc.channel[2].raw) * adc_scale) * iout_scale
    vin = (float(myadc.channel[3].raw) * adc_scale) * vin_scale
    vout = (float(myadc.channel[4].raw) * adc_scale) * vout_scale
    ilim_pos = (float(myadc.channel[5].raw) * adc_scale) * ilim_pos_scale
    vpot_pos = (float(myadc.channel[6].raw) * adc_scale) * vpot_pos_scale



    print("Initial Board conditions:")
    print("U2 Temperature: " + str(ldoU2_temp) + " C")
    print("U3 Temperature: " + str(ldoU3_temp) + " C")
    print("Output Current: " + str(iout) + " A")
    print("Input Voltage: " + str(vin) + " V")
    print("Output Voltage: " + str(vout) + " V")
    print("ILIM pot position: " + str(ilim_pos) + " %")
    print("Vout pot position: " + str(vpot_pos) + " %")

# Trisha, here is where to put the production test code.
    print("\n\nStarting Production Test! Connect Fluke 87 or equivalent meter")
    print("to output jacks. Do not connect any additional load")
    failed_tests = []
    # Test zero output (verifies negative supply and current sink)
    setpoint = 0.0
    mydac.raw = str(int(setpoint * 1000.0 / (11.0 *dac_scale)))
    time.sleep(0.1)
    vout = (float(myadc.channel[4].raw) * adc_scale) * vout_scale
    if (-0.01 < vout < 0.01):
        print("Zero output voltage: %.3f, test PASSES!" % (vout))
    else:
        print("Zero output voltage test FAILS!")
        failed_tests.append("Fails zero output test")

    # Prompt user to Set both potentiometers to 50% scale.
    # Set output voltage to 18V by writing to the DAC
    # Verify potentiometer positions are actually between 40% and 60% (okay
    # to have a wide tolerance on this...
    # Verify output voltage is LESS THAN 16V. This verifies that precision diode
    # OR circuit is operating correctly.
    input("\nSet both potentiometers to 3:45 position, then press enter to continue...")
    setpoint = 18.0
    mydac.raw = str(int(setpoint * 1000.0 / (11.0 *dac_scale)))
    time.sleep(0.1)

    ilim_pos = (float(myadc.channel[5].raw) * adc_scale) * ilim_pos_scale
    vpot_pos = (float(myadc.channel[6].raw) * adc_scale) * vpot_pos_scale
    while (ilim_pos < 40) or (ilim_pos >60) or (vpot_pos <40) or (vpot_pos > 60):
        print("Pot positions fail!")
        print("Ilim pot position: " + str(ilim_pos) + " %")
        print("Vout pot position: " + str(vpot_pos) + " %")
        input("\nSet both potentiometers to 3:45 position, then press enter to continue...")
        time.sleep(0.1)
        ilim_pos = (float(myadc.channel[5].raw) * adc_scale) * ilim_pos_scale
        vpot_pos = (float(myadc.channel[6].raw) * adc_scale) * vpot_pos_scale
    else:
        print("Ilim pot position: " + str(ilim_pos) + " %, ILIM POT PASS!")
        print("Vout pot position: " + str(vpot_pos) + " %, Vout POT PASS!")
    
    vout = (float(myadc.channel[4].raw) * adc_scale) * vout_scale
    if (vout < 16):
        print("Output voltage: %.3f, test PASSES!" % (vout))
    else:
        print("Precision diode OR circuitry FAILS!")
        failed_tests.append("Fails OR circuit test")

    # (implement test here...)

    # Prompt user to connect 4-ohm, 50W resistor ON A HEAT SINK to output.
    # The output will go into current limit of about 1.5A, and the LDOs will
    # start to heat up.
    # Insert 5 second delay.
    # Verify output current between 1A and 2A (we'll determine exact limits as
    # we gain experience.)
    # Verify BOTH LDO temperatures are greater than 60C (we may have to adjust this limit)
    # (implement test here...)

    input("\nConnect a 4-ohm, 50W resistor ON A HEAT SINK to output of the board, then press enter to continue...")
    time.sleep(5)
    iout = (float(myadc.channel[2].raw) * adc_scale) * iout_scale
    if (1 < iout < 2):
        print("Current limit test PASS!")
    else:
        print("Current limit test FAILS")
        failed_tests.append("Fails current limit test")

    print("Setting DAC output to zero, just to be safe...\n\n")
    mydac.raw = "0"

    del myadc
    del mydac
    if len(failed_tests) == 0:
        print("Board PASSES!!")
    else:
        print("Board FAILED the following tests:")
        for failure in failed_tests:
            print(failure)
        print("Note failures and set aside for debug.")


if __name__ == '__main__':
    hardcoded_ip = 'ip:172.20.10.7' #118
    my_ip = sys.argv[1] if len(sys.argv) >= 2 else hardcoded_ip
    print("Connecting with CN0508 context at %s" % (my_ip))


    testdata = main(my_ip)