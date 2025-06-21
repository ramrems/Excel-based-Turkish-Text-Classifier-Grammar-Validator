import tkinter as tk # Tkinter GUI kütüphanesi arayüzü için
from tkinter import filedialog, messagebox, scrolledtext # Dosya seçme, hata mesajı ve kaydırmalı metin kutusu için
import pandas as pd # Excel dosyası okuma ve veri işleme için
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification,AutoModelForTokenClassification # Hugging Face modelleri ve pipeline için
import torch 
import re # Metni cümlelere ayırırken kullandık.

# 3 farklı model için 3 farklı tokenizer'ı yükleyeceğiz.


tokenizer = AutoTokenizer.from_pretrained("ennp/bert-turkish-text-classification-cased")
politics_tokenizer = AutoTokenizer.from_pretrained("savasy/bert-turkish-text-classification")#
grammar_tokenizer = AutoTokenizer.from_pretrained("GGLab/gec-tr-seq-tagger")

#Hugging Face'den yüklenen modeller 
model = AutoModelForTokenClassification.from_pretrained("GGLab/gec-tr-seq-tagger") #Dil bilgisi modeli
model1 = AutoModelForSequenceClassification.from_pretrained("ennp/bert-turkish-text-classification-cased") #INSULT', 'RACIST', 'SEXIST', 'PROFANITY','OTHER' etiketlerine sahip metinleri tespti edebilir.
model2 = AutoModelForSequenceClassification.from_pretrained("savasy/bert-turkish-text-classification") #politics etiketine sahip metinleri tespit edebilir.

nlp = pipeline("sentiment-analysis", model=model1, tokenizer=tokenizer)
nlp2 = pipeline("text-classification", model=model2, tokenizer=politics_tokenizer)

# Etiketlerin metin karşılıkları
code_to_label = {
    'LABEL_0': 'INSULT',
    'LABEL_1': 'RACIST',
    'LABEL_2': 'SEXIST',
    'LABEL_3': 'PROFANITY',
    'LABEL_4': 'OTHER'
}

def browse_file(): #Excel dosyası seçmek için dosya seçme penceresi açar.
    filepath = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
    )
    if filepath:
        file_path_var.set(filepath)

def metni_cumlelere_ayir(metin):
    # Noktadan sonra büyük harfle başlayan cümleleri yakalayarak bölme işlemi yapıyoruz
    cumleler = re.split(r'(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ])', metin)
    return cumleler

def analyze_grammar(): #Dil bilgisi kontrolü yapar.
    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)

    filepath = file_path_var.get()
    if not filepath:
        messagebox.showerror("Hata", "Lütfen bir dosya seçin.")
        return

    try:
        # Excel dosyasını oku ve 'Mesaj Metni' sütununu al
        df = pd.read_excel(filepath, usecols=["Mesaj Metni"])
        inappropriate_sentences = []

        # Her bir metin satırı üzerinde analiz yap
        for index, row in df.iterrows():
            text = row["Mesaj Metni"]
            if pd.notna(text):
                # Metni kelimelere ayır ve tamamen büyük harfli kelimeleri atla
                words = text.split()
                filtered_text = ' '.join([word for word in words if not buyuk_harf(word)])
                
                # Eğer geriye hiç kelime kalmadıysa cümleyi atla
                if not filtered_text.strip():
                    continue

                # Metni tokenlere ayırın ve modelin anlayacağı formata dönüştürün
                inputs = grammar_tokenizer(filtered_text, return_tensors="pt")

                # Modelin tahmin yürütmesi
                outputs = model(**inputs)

                # Tahmin edilen etiketleri çıkarın
                logits = outputs.logits
                predictions = torch.argmax(logits, dim=2)

                # Tokenleri ve tahmin edilen etiketleri al
                tokens = grammar_tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
                predicted_labels = predictions[0].numpy()

                # Cümlenin uygun olup olmadığını kontrol etme
                sentence_is_appropriate = all(label == 0 for label in predicted_labels)

                # Eğer cümle uygunsuzsa sonuçları listeye ekle
                if not sentence_is_appropriate:
                    inappropriate_sentences.append({
                        "Satır No": index + 2, # Kod Excel satır numarasını oluştururken ilk baştaki sütun başlığını almadığı için ve numaralandırmaya sıfırdan başladığı için +2 ekliyoruz
                        "Metin": text,
                        "Tokens": tokens,
                        "Labels": predicted_labels
                    })

        # Sonuçları göster
        display_grammar_results(inappropriate_sentences) 

    except Exception as e:
        print("HATA: ", e)
        messagebox.showerror("Hata", f"Dosya işlenirken bir hata oluştu: {e}")

def buyuk_harf(word): #Kelimenin tamamen büyük harfli olup olmadığını kontrol eder.
    return word.isupper()

def highlight_offending_words(uygunsuz_metinler): #Uygunsuz metinleri renklendirir.
    highlighted_results = []

    for item in uygunsuz_metinler:
        cumle = item["Metin"]
        tokens = cumle.split()  # Cümleyi kelimelere böl
        tokens_with_labels = []  # Renklendirme için kelimeleri saklayacağımız liste

        # Her bir kelimeyi ayrı ayrı etiketleyip kontrol ediyoruz
        for token in tokens:
            sonuc = nlp(token)  # Her kelimeyi etiketle
            etiket = code_to_label.get(sonuc[0]['label'], 'OTHER')
            score = sonuc[0]['score']

            # Uygunsuz kelimeyi renklendirilecek olarak işaretle
            if etiket in ['INSULT', 'RACIST', 'SEXIST', 'PROFANITY'] and score >= 0.55:
                tokens_with_labels.append({"text": token, "score": score, "label": "red"})
            elif etiket in ['INSULT', 'RACIST', 'SEXIST', 'PROFANITY']:
                tokens_with_labels.append({"text": token, "score": score, "label": "lightred"})
            else:
                tokens_with_labels.append({"text": token, "score": score, "label": "default"})

        highlighted_results.append({
            "Satır No": item["Satır No"],
            "Metin": cumle,
            "Tokens": tokens_with_labels,
            "Sonuç": item["Sonuç"],
            "Skor": item["Skor"],
        })

    return highlighted_results
    
def analyze_text_class(): #Uygunsuz metin kontrolü yapar.   
    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)

    filepath = file_path_var.get()
    if not filepath:
        messagebox.showerror("Hata", "Lütfen bir dosya seçin.")
        return
    
    try:
        df = pd.read_excel(filepath, usecols=["Mesaj Metni"])
        uygunsuz_metinler = []

        for index, row in df.iterrows():
            metin = row["Mesaj Metni"]
            
            # Metin türünü kontrol et ve boş değerleri atla
            if not isinstance(metin, str): # Eğer metin bir string değilse
                if pd.notna(metin):
                    metin = str(metin)
                else:
                    continue
            
            cumleler = metni_cumlelere_ayir(metin)

            if pd.notna(metin):
                # Genel metin için uygunsuzluk kontrolü
                sonuc = nlp(metin)
                etiket = code_to_label.get(sonuc[0]['label'])
                score = sonuc[0]['score']

                # Metni genel etiketine göre kontrol et
                if etiket != 'OTHER':
                    uygunsuz_metinler.append({
                        "Satır No": index + 2,
                        "Metin": metin,
                        "Sonuç": etiket,
                        "Skor": round(score, 2)
                    })

                # Cümleleri ayrı ayrı incele
                for cumle in cumleler:
                    if pd.notna(cumle): # Boş cümleleri atlar
                        sonuc_politics = nlp2(cumle)
                        # İkinci modelin etiketleriyle eşleşen sözlüğü doğru kullanın
                        etiket_politics = sonuc_politics[0]['label']
                        score_politics = sonuc_politics[0]['score']

                        if etiket_politics == 'politics':
                            uygunsuz_metinler.append({
                                "Satır No": index + 2,
                                "Metin": metin,
                                "Sonuç": etiket_politics,
                                "Skor": round(score_politics, 2)
                            })

        # Kelimeleri renklendir ve sonuçları göster
        highlighted_metinler = highlight_offending_words(uygunsuz_metinler)
        display_results(highlighted_metinler)

    except Exception as e:
        print("HATA: ", e)
        messagebox.showerror("Hata", f"Dosya işlenirken bir hata oluştu: {e}")

# Renkleri göstermek için güncellenmiş `display_results` fonksiyonu
def display_results(results):
    result_text.delete(1.0, tk.END)
    if results:
        for item in results:
            result_text.insert(tk.END, f"Satır {item['Satır No']} :\n")

            # Metindeki tokenleri renklendirme
            for token_info in item['Tokens']:
                token = token_info['text']
                tag = token_info['label']

                # Uygun renkte gösterimi
                result_text.insert(tk.END, f"{token} ", tag)

            result_text.insert(tk.END, f" - Sonuç: {item['Sonuç']} {item['Skor']}\n\n")

    else:
        result_text.insert(tk.END, "Uygunsuz metin bulunamadı.")

def display_grammar_results(results): #Dil bilgisi kontrolü sonuçlarını gösterir.
    result_text.config(state=tk.NORMAL)
    result_text.delete("1.0", tk.END)
    if results:
        for item in results:
            text = item['Metin']
            result_text.insert(tk.END, f"Satır {item['Satır No']}:\n")
            
            # Orijinal metin üzerinde tokenleri bulup renklendirme
            start = 0
            for token, label in zip(item['Tokens'], item['Labels']):
                token_clean = re.sub(r"##", "", token)  # Tokenlerden `##` sembolünü temizle
                token_pos = text.find(token_clean, start)
                # Eğer token bulunmuşsa, metni renklendir
                if token_pos != -1:
                    # Hatalı kısımları renklendir
                    if label != 0:
                        result_text.insert(tk.END, text[start:token_pos])
                        result_text.insert(tk.END, text[token_pos:token_pos+len(token_clean)], "red")
                        start = token_pos + len(token_clean)
                    else:
                        result_text.insert(tk.END, text[start:token_pos+len(token_clean)])
                        start = token_pos + len(token_clean)

            # Kalan metni ekleyin
            result_text.insert(tk.END, text[start:] + "\n\n")
    else:
        result_text.insert(tk.END, "Dilbilgisi hatalı metin bulunamadı.")
    result_text.config(state=tk.DISABLED)

# Tkinter GUI oluşturma
root = tk.Tk()
root.title("Excel Dosyası Analiz Aracı")

# Ana pencerenin boyutlandırılabilir olduğunu belirtir
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Ana çerçeve
frame = tk.Frame(root)
frame.grid(sticky="nsew", pady=10, padx=10)

# Çerçevenin içeriklerinin boyutlandırılabilir olduğunu belirtir
frame.grid_rowconfigure(2, weight=1)
frame.grid_columnconfigure(1, weight=1)

file_path_var = tk.StringVar()

# Gözat bölümü
tk.Label(frame, text="Excel Dosyasını Seçin:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
tk.Entry(frame, textvariable=file_path_var, width=50).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
tk.Button(frame, text="Gözat", command=browse_file).grid(row=0, column=2, padx=5, pady=5, sticky="e")

# Uygunsuz metin kontrol et ve Dil bilgisi kontrol et butonları
button_frame = tk.Frame(frame)
button_frame.grid(row=1, column=0, columnspan=3, pady=10)

tk.Button(button_frame, text="Uygunsuz metin kontrol et", command=analyze_text_class, width=20).pack(side="left", padx=5)
tk.Button(button_frame, text="Dil Bilgisi kontrol et", command=analyze_grammar, width=20).pack(side="left", padx=5)

# Sonuçlar için kaydırmalı metin kutusu
result_text = scrolledtext.ScrolledText(frame, width=80, height=20)
result_text.grid(row=2, column=0, columnspan=3, pady=10, sticky="nsew")

# Kırmızı renk için etiket ayarı
result_text.tag_configure("red", foreground="red")
# Tag renk ayarları
result_text.tag_configure("darkred", foreground="#8B0000")  # Koyu kırmızı
result_text.tag_configure("lightred", foreground="#FF6347")  # Açık kırmızı
result_text.tag_configure("default", foreground="black")  # Varsayılan siyah

root.mainloop()

