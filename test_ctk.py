import customtkinter as ctk

app = ctk.CTk()
app.geometry("400x300")

scroll = ctk.CTkScrollableFrame(app)
scroll.pack(fill="both", expand=True)

for i in range(5):
    btn = ctk.CTkButton(scroll, text=f"Button {i}")
    btn.pack(pady=10)

app.update_idletasks()

try:
    print("bbox:", scroll._parent_canvas.bbox("all"))
except Exception as e:
    print("Error:", e)

app.destroy()
