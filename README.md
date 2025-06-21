# Mesaj Analiz

Bu proje, mesaj metinlerini analiz ederek uygunsuz içerikleri ve dil bilgisi hatalarını tespit eden bir masaüstü uygulamasıdır. Uygulama, Hugging Face platformundan indirilen hazır modeller ile Türkçe metinler üzerinde analiz gerçekleştirir.

## Kullanılan Modeller

1. **ennp/bert-turkish-text-classification-cased**  
   - Metinleri 5 farklı kategoriye ayıran bir sınıflandırma modelidir.
   - `OTHER` dışındaki etiketler uygunsuz olarak değerlendirilir.

2. **savasy/bert-turkish-text-classification**  
   - Farklı kategorilerde sınıflandırma yapar.
   - Bu projede yalnızca `politics` etiketi kullanılmıştır.
   - Politik içerikler uygunsuz kabul edilir.

3. **GGLab/gec-tr-seq-tagger**  
   - Türkçe dil bilgisi hatalarını token bazında tespit eden bir modeldir.
   - Hatalı kelimeler tespit edilerek kullanıcıya gösterilir.

## Arayüz Özellikleri

Uygulama arayüzü `Tkinter` ile geliştirilmiş olup üç temel buton içerir:

- **Gözat**: Analiz edilecek Excel dosyasını seçer.
- **Uygunsuz metin kontrol et**:  
  - Mesajları sınıflandırır.  
  - `OTHER` dışındaki etiketler veya `politics` içerenler renklendirilerek gösterilir.  
  - %50 üzeri skorlar koyu kırmızı, altı açık kırmızı ile belirtilir.
- **Dil bilgisi kontrol et**:  
  - Dil bilgisi hatalarını tespit eder.  
  - Hatalı kelimeler doğrudan renklendirilerek sunulur.  
  - Token işleminden doğan `#` karakterleri temizlenir.

## Teknik Notlar

- Arayüzde renklendirme, konumlandırma ve ekran esnekliği sağlanmıştır.
- Uygulama kısa sürede geliştirildiğinden hazır modeller tercih edilmiştir. İleri çalışmalarda özel bir model eğitilerek daha iyi sonuçlar elde edilebilir.

## Kurulum

1. Gerekli bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
