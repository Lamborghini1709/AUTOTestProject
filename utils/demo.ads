; [HiSi] HBT Case 1 (Using ADS HBT Builtin Model)

; Options
Options:Options1 \
 V_RelTol=1e-6 I_RelTol=1e-6 V_AbsTol=1e-6 I_AbsTol=1e-12 \
 Temp=25 Tnom=25 Gmin=1e-12 \
 ASCII_Rawfile=yes NumDigitsInRawfile=14

; Parameters
Pavs=0
RFfreq=1
ACfreq=1

; Models
simulator lang=spectre
global 0
include "../model/ads_hbt.1.modelcard"
simulator lang=ads

#uselib "ckt", "INDQ_Z"

; Circuit
Port:PORT1 N__0 0 Num=1 Z=50 Ohm Noise=yes \
 P[1]=dbmtow(Pavs) Freq[1]=RFfreq GHz
Port:Term2 Vload 0 Num=2 Z=50 Ohm Noise=yes

I_Source:SRC5 N__0 Vinput Type="I_1Tone" \
 I[1]=1 A Freq[1]=ACfreq GHz Iac=polar(1,0) mA

V_Source:SRC2 Vcc 0 Type="V_DC" Vdc=5 V
V_Source:SRC3 N__15 0 Type="V_DC" Vdc=3.2 V

R:R4 N__15 N__22 R=10 Ohm Noise=yes
R:R6 N__16 T_b R=50 Ohm Noise=yes

CAPQ:C2 T_c 0 C=2.2 pF Q=50.0 F=1000.0 MHz Mode=1
CAPQ:C3 N__22 0 C=10 pF Q=50.0 F=1000.0 MHz Mode=1
CAPQ:C4 Vload N__21 C=3.5 pF Q=50.0 F=1000.0 MHz Mode=1
CAPQ:C5 T_b Vinput C=20 pF Q=50.0 F=1000.0 MHz Mode=1
CAPQ:C6 Vload 0 C=50 fF Q=50.0 F=1000.0 MHz Mode=1
CAPQ:C7 Vcc 0 C=50 fF Q=50.0 F=1000.0 MHz Mode=1

INDQ_Z:L2 N__21 T_c L=16 nH Q=50.0 F=1000.0 MHz Mode=1 Rdc=0.0 Ohm
INDQ_Z:L3 T_c Vcc L=16 nH Q=50.0 F=1000.0 MHz Mode=1 Rdc=0.0 Ohm
INDQ_Z:L4 T_e 0 L=5 pH Q=50.0 F=1000 MHz Mode=1 Rdc=0.0 Ohm

Short:Iinput Vinput N__14 Mode=0 SaveCurrent =yes
Short:Iload N__6 Vload Mode=0 SaveCurrent=yes
Short:Icc Vcc N__2 Mode=0 SaveCurrent=yes

"HBTM1":HBT1 T_c T_b T_e Mode=1 Noise=yes SelfTmod=0
"HBTM1":HBT2 N__15 N__22 N__16 Mode=1 Noise=yes SelfTmod=0
"HBTM1":HBT3 N__22 N__22 N__5 Mode=1 Noise=yes SelfTmod=0
"HBTM1":HBT4 N__5 N__5 0 Mode=1 Noise=yes SelfTmod=0

; Analysis
AC:AC1 \
 SweepVar="freq" \
 SweepPlan="AC1_stim"

SweepPlan:AC1_stim \
 Start=ACfreq GHz \
 Stop=(10*ACfreq) GHz \
 Step=ACfreq GHz

; HB 
; HB:HB1 \
;  Freq[1]=1 GHz \
;  Order[1]=5 \
;  UseKrylov=1 \
;  KrylovPrec=1 \
;  SS_Plan="HB1_stim"
;  
; SweepPlan:HB1_stim \
;  Start=10 MHz \
;  Stop=(2*ACfreq) GHz \
;  Step=10 MHz
