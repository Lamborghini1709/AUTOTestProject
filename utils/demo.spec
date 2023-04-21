// Haisi HBT Case:HBT_simple_1T （va）

// Options
// Options

// Parameters
parameters Pavs=0
parameters Rfreq=1.0

// Models





// Circuit
Cdc_block1 ( N__12 N__0 ) capacitor c=1u
Riinput ( Vinput N__12 ) resistor r=0
Rioad ( N__14 Vload ) resistor r=0
Ldc_feed1 ( N__15 N__0 ) inductor l=1u
Ricc ( Vcc N__2 ) resistor r=0
Cdc_block2 ( N__21 N__14 ) capacitor c=1u
Ricc1 ( Vb N__15 ) resistor r=0
Ldc_feed2 ( N__2 N__17 ) inductor l=1u

HBT1 ( N__17 N__0 0 ) HBTM1 isnoisy=yes temp=25 tnom=25

Pport1 ( Vinput 0 ) port r=50.0
Pterm2 ( Vload 0 ) port r=50.0

Vsrc2 ( Vcc 0 ) vsource type=dc v=5.0
Vsrc3 ( Vb 0 ) vsource type=dc v=1.32

Cc2 ( N__17 0 ) capq c=1.1p q=50.0 fq=1000.0M mode=1


Ll2 ( N__21 N__17 ) inductor l=15.0n q=50.0 fq=1000.0M mode=1 rdc=0.0Ohm






//SweepPlan: SP1_stim Start=1.0 GHz Stop=10.0 GHz Step=0.1 GHz

// OutputPlan

//HB:HB2  MaxOrder=4 Freq[1]=Rfreq GHz Order[1]=5  StatusLevel=2 Restart=no CalcS_Params=yes  LSSP_FreqAtPort[1]=Rfreq GHz  LSSP_FreqAtPort[2]=Rfreq GHz  SweepVar="Rfreq" SweepPlan="HB2_stim" OutputPlan="HB2_Output"

//SweepPlan: HB2_stim Start=1 Stop=10 Step=0.1

// OutputPlan
