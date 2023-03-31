// [HiSi] HBT Case 1 (Using ADS HBT Builtin Model)

// Options
// Options

// Parameters
parameters Pavs=0
parameters RFfreq=1
parameters ACfreq=1

// Models





//model HBTM1 ADSHBT



// Circuit
Pport1 ( N__0 0 ) port r=50.0
Pterm2 ( Vload 0 ) port r=50.0

Isrc5 ( N__0 Vinput ) isource type=sine

Vsrc2 ( Vcc 0 ) vsource type=dc v=5.0
Vsrc3 ( N__15 0 ) vsource type=dc v=3.2

Rr4 ( N__15 N__22 ) resistor r=10.0 isnoisy=yes
Rr6 ( N__16 T_b ) resistor r=50.0 isnoisy=yes

Cc2 ( T_c 0 ) capq c=2.2p q=50.0 fq=1000.0M mode=1
Cc3 ( N__22 0 ) capq c=10.0p q=50.0 fq=1000.0M mode=1
Cc4 ( Vload N__21 ) capq c=3.5p q=50.0 fq=1000.0M mode=1
Cc5 ( T_b Vinput ) capq c=20.0p q=50.0 fq=1000.0M mode=1
Cc6 ( Vload 0 ) capq c=50.0f q=50.0 fq=1000.0M mode=1
Cc7 ( Vcc 0 ) capq c=50.0f q=50.0 fq=1000.0M mode=1

Ll2 ( N__21 T_c ) inductor l=16.0n q=50.0 fq=1000.0M mode=1 rdc=0.0Ohm
Ll3 ( T_c Vcc ) inductor l=16.0n q=50.0 fq=1000.0M mode=1 rdc=0.0Ohm
Ll4 ( T_e 0 ) inductor l=5.0p q=50.0 fq=1000MHZ mode=1 rdc=0.0Ohm

Riinput ( Vinput N__14 ) resistor r=0
Riload ( N__6 Vload ) resistor r=0
Ricc ( Vcc N__2 ) resistor r=0

HBT1 ( T_c T_b T_e ) HBTM1 isnoisy=yes temp=25 tnom=25
HBT2 ( N__15 N__22 N__16 ) HBTM1 isnoisy=yes temp=25 tnom=25
HBT3 ( N__22 N__22 N__5 ) HBTM1 isnoisy=yes temp=25 tnom=25
HBT4 ( N__5 N__5 0 ) HBTM1 isnoisy=yes temp=25 tnom=25

// Analysis
//AC:AC1  SweepVar="freq"  SweepPlan="AC1_stim"

//SweepPlan:AC1_stim  Start=ACfreq GHz  Stop=(10*ACfreq) GHz  Step=ACfreq GHz

// HB
// HB:HB1 ; Freq[1]=1 GHz ; Order[1]=5 ; UseKrylov=1 ; KrylovPrec=1 ; SS_Plan="HB1_stim"
parameters ;
// SweepPlan:HB1_stim ; Start=10 MHz ; Stop=(2*ACfreq) GHz ; Step=10 MHz
