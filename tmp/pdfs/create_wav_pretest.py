from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

W, H = letter
navy, blue, pale, line, text, muted, orange, green = map(HexColor, ["#112d47", "#2878ea", "#eaf3ff", "#d7e1ec", "#17324e", "#6684a5", "#d97706", "#178b4d"])
c = Canvas("output/pdf/recorded-wav-pretest.pdf", pagesize=letter)

def box(x,y,w,h,fill=white,stroke=line,r=10):
    c.setFillColor(fill); c.setStrokeColor(stroke); c.roundRect(x,y,w,h,r,fill=1,stroke=1)
def label(x,y,s): c.setFillColor(blue); c.setFont("Helvetica-Bold",10); c.drawString(x,y,s.upper())
def txt(x,y,s,size=10,color=text,font="Helvetica"):
    c.setFillColor(color); c.setFont(font,size); c.drawString(x,y,s)
def arrow(x1,y,x2):
    c.setStrokeColor(HexColor("#4a6b89")); c.setLineWidth(2); c.line(x1,y,x2,y); c.line(x2,y,x2-6,y+3); c.line(x2,y,x2-6,y-3)

c.setFillColor(navy); c.rect(0,H-112,W,112,fill=1,stroke=0)
txt(54,H-33,"LOCAL LIVE AUDIO TRANSLATION",10,HexColor("#bcd7fb"),"Helvetica-Bold")
txt(54,H-63,"Recorded WAV Pre-Test",25,white,"Helvetica-Bold")
txt(54,H-84,"Repeatable VAD and Whisper evaluation before live cable testing",11,HexColor("#d8e7f7"))
box(465,H-80,95,34,HexColor("#194a70"),HexColor("#194a70"),18); txt(478,H-66,"STATUS: COMPLETE",8,HexColor("#bff0d3"),"Helvetica-Bold")

box(54,H-182,504,48,pale,pale,10); label(70,H-151,"Goal"); txt(70,H-170,"Turn an English video into stable evaluation inputs, then compare local WebRTC and stateful Silero VAD.",10)

box(54,H-430,504,218,HexColor("#f8fbff"),line,10); label(70,H-238,"Recorded evaluation path"); txt(70,H-256,"One local source, identical WAV/SRT reference, separate backend artifacts.",9,muted)
box(70,H-360,118,55,white,line,8); txt(82,H-326,"Video",11,text,"Helvetica-Bold"); txt(82,H-343,".mp4",10,muted); c.setFillColor(blue); c.rect(145,H-350,25,18,fill=1,stroke=0); c.setFillColor(white); c.circle(156,H-341,4,fill=1,stroke=0)
box(215,H-360,118,55,white,line,8); txt(230,H-326,"Extract",11,text,"Helvetica-Bold"); txt(230,H-343,"audio + captions",9,muted); c.setFillColor(orange); c.circle(302,H-341,10,fill=1,stroke=0); txt(298,H-345,"↓",13,white,"Helvetica-Bold")
box(360,H-360,178,55,white,line,8); txt(374,H-326,"Evaluation inputs",11,text,"Helvetica-Bold"); txt(374,H-343,"16 kHz mono WAV + English SRT",8,muted)
arrow(188,H-337,215); arrow(333,H-337,360)

box(70,H-427,468,55,HexColor("#e7f1ff"),HexColor("#a9cdfd"),8); txt(84,H-395,"WAV + SRT",11,text,"Helvetica-Bold"); arrow(166,H-399,230); txt(242,H-395,"VAD",11,blue,"Helvetica-Bold"); txt(242,H-412,"WebRTC or stateful Silero",8,muted); arrow(337,H-399,390); txt(401,H-395,"Whisper on Metal",11,text,"Helvetica-Bold"); txt(401,H-412,"transcript + report",8,muted)

box(54,H-590,238,126,white,line,10); label(70,H-489,"What we measure"); txt(70,H-513,"• Phrase timing and boundaries",10); txt(70,H-534,"• Transcript continuity",10); txt(70,H-555,"• Subtitle comparison report",10)
box(320,H-590,238,126,white,line,10); label(336,H-489,"Recorded results - 120 s"); txt(336,H-513,"Speaker 1: WebRTC 92.2% | Silero 91.4%",9,text,"Helvetica-Bold"); txt(336,H-534,"Speaker 2: WebRTC 90.7% | Silero 90.1%",9,text,"Helvetica-Bold"); txt(336,H-555,"Silero: clean, non-overlapping phrases",10,green,"Helvetica-Bold")

box(54,H-696,504,72,navy,navy,10); label(70,H-648,"Next step"); txt(70,H-673,"Use recorded comparison to tune phrase cadence.",11,white,"Helvetica-Bold"); txt(70,H-690,"Then validate both modes live with the correct cable.",11,white,"Helvetica-Bold")
txt(54,39,"Pre-test note: subtitle similarity is approximate; listening quality and live cadence still require field validation.",8,muted,"Helvetica-Oblique")
txt(54,20,"Audio Translation - Recorded WAV Pre-Test",8,text,"Helvetica-Bold"); txt(535,20,"1 / 1",8,muted)
c.save()
