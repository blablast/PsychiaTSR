# 🧠 Psychia - Asystent Terapii TSR

**Inteligentny asystent do terapii Solution-Focused Brief Therapy (TSR) z wykorzystaniem sztucznej inteligencji**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39+-red.svg)](https://streamlit.io)

## 📋 Spis treści

- [🎯 O aplikacji](#-o-aplikacji)
- [✨ Funkcjonalności](#-funkcjonalności)
- [🚀 Instalacja](#-instalacja)
- [⚙️ Konfiguracja](#️-konfiguracja)
- [💻 Użycie](#-użycie)
- [🤖 Modele AI](#-modele-ai)
- [🧪 Testowanie modeli](#-testowanie-modeli)
- [🔧 Pliki konfiguracyjne](#-pliki-konfiguracyjne)

## 🎯 O aplikacji

Psychia to zaawansowany asystent terapeutyczny wykorzystujący **Solution-Focused Brief Therapy (TSR)** - metodę terapii skupioną na rozwiązaniach. Aplikacja oferuje:

- **Profesjonalną terapię TSR** prowadzoną przez AI
- **Dwuagentowy system** z terapeutą i supervisorem
- **Protokoły bezpieczeństwa** dla sytuacji kryzysowych
- **Obsługę różnych modeli AI** (OpenAI, Google Gemini)
- **Zaawansowane testowanie** jakości modeli

## ✨ Funkcjonalności

### 🎭 **Dwuagentowy System AI**
- **🩺 Terapeuta AI**: Prowadzi rozmowę według zasad TSR
- **👥 Supervisor AI**: Ocenia postępy i decyduje o przejściach między etapami
- **🧠 Inteligentna pamięć**: Optymalne zarządzanie kontekstem rozmowy

### 📋 **Etapy Terapii TSR**
1. **🤝 Otwarcie i określenie celu** (10-15 min) - Powitanie i precyzyjne określenie celu sesji
2. **💎 Zasoby i wyjątki** (15-20 min) - Odkrywanie mocnych stron i momentów bez problemu
3. **📊 Skale** (10-15 min) - Ocena obecnej sytuacji i wizualizacja poprawy
4. **👣 Małe kroki i działania** (15-20 min) - Planowanie konkretnych kroków do celu
5. **🎊 Podsumowanie i wzmocnienie** (10-15 min) - Wzmocnienie postępów i motywacji

### 🚨 **Bezpieczeństwo**
- **Automatyczna detekcja** sytuacji kryzysowych
- **Protokół kryzysowy** z numerami pomocy
- **Monitorowanie bezpieczeństwa** w czasie rzeczywistym

### 🤖 **Obsługa Modeli AI**
- **🌐 OpenAI**: GPT-4o, GPT-4o-mini, GPT-4, GPT-3.5-turbo
- **🧠 Google Gemini**: gemini-1.5-flash, gemini-1.5-pro, gemini-pro
- **🔍 Automatyczne wykrywanie** dostępnych modeli
- **💾 Inteligentny cache** z odświeżaniem co 7 dni

### 🧪 **Testowanie Modeli**
- **💬 Tryb czatu**: Proste testowanie konwersacji
- **🧠 Test pamięci**: Zaawansowane sprawdzanie zdolności modelu
- **📊 Analiza wyników**: Automatyczne rekomendacje konfiguracji

### 🔧 **Zaawansowane Logowanie**
- **📝 Szczegółowe logi** wszystkich interakcji
- **📋 Kopiowanie bloków** według rozmów użytkownika
- **🎯 Śledzenie etapów** w czasie rzeczywistym
- **🔍 Podgląd promptów** w rozwijaných kontenerach

## 🚀 Instalacja

### Wymagania
- **Python 3.12+**
- **4GB RAM** (dla modeli chmurowych)
- **Klucze API** OpenAI lub Google Gemini

### Kroki instalacji

```bash
# 1. Pobierz aplikację
git clone https://github.com/your-username/psychia.git
cd psychia

# 2. Utwórz środowisko wirtualne
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Zainstaluj wymagania
pip install -r requirements.txt

# 4. Uruchom aplikację
streamlit run app.py
```

## ⚙️ Konfiguracja

### Klucze API - plik `.env`

Utwórz plik `.env` w katalogu głównym:

```bash
# OpenAI (zalecane)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Google Gemini (alternatywa)
GOOGLE_API_KEY=your-google-api-key-here
```

**Gdzie uzyskać klucze:**
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Google Gemini**: [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

### Konfiguracja w aplikacji

Wszystkie pozostałe ustawienia można zmienić w interfejsie aplikacji:
- **Wybór modeli** dla terapeuty i supervisora
- **Parametry generowania** (temperatura, max tokens)
- **Ustawienia bezpieczeństwa**
- **Opcje logowania**

## 💻 Użycie

### Szybki start

1. **Uruchom aplikację**:
   ```bash
   streamlit run app.py
   ```

2. **Wprowadź klucze API** w pasku bocznym

3. **Wybierz modele** dla terapeuty i supervisora

4. **Rozpocznij rozmowę** - napisz pierwszą wiadomość!

### Interfejs aplikacji

#### **💬 Główne okno**
- **Czat**: Rozmowa z terapeutą AI
- **Informacja o etapie**: Aktualny etap terapii
- **Kontrola etapów**: Możliwość ręcznej zmiany etapu

#### **🔧 Logi techniczne**
- **Kopiowanie bloków**: Każdą rozmowę można skopiować
- **Rozwijane szczegóły**: Pełne prompty i odpowiedzi
- **Kolorowe oznaczenia**: Różne typy wiadomości
- **Historia bez limitów**: Wszystkie rozmowy są zapisywane

#### **⚙️ Pasek boczny**
- **Klucze API**: Wprowadzanie i weryfikacja
- **Wybór modeli**: Dynamiczna lista dostępnych modeli
- **Parametry**: Temperatura, długość odpowiedzi
- **Status**: Informacje o połączeniu z modelami

## 🤖 Modele AI

### Zalecane konfiguracje

#### **🏆 Konfiguracja Idealna**
- **Terapeuta**: `gpt-4o`
- **Supervisor**: `gpt-4o-mini`
- **Koszt**: ~$0.01-0.05 za sesję
- **Jakość**: Najwyższa

#### **⚡ Konfiguracja Ekonomiczna**
- **Terapeuta**: `gpt-4o-mini`
- **Supervisor**: `gpt-4o-mini`
- **Koszt**: ~$0.001-0.01 za sesję
- **Jakość**: Bardzo dobra

#### **🧠 Konfiguracja Gemini**
- **Terapeuta**: `gemini-1.5-pro`
- **Supervisor**: `gemini-1.5-flash`
- **Koszt**: ~$0.001-0.02 za sesję
- **Jakość**: Dobra alternatywa

### Status modeli w aplikacji
- ✅ **Dostępny**: Model gotowy do użycia
- ⚠️ **Wymaga klucza**: Wprowadź klucz API
- ❌ **Niedostępny**: Model nie jest obsługiwany

## 🧪 Testowanie modeli

### Test pamięci modelu

Aplikacja zawiera zaawansowany system testowania:

#### **🔬 5-stopniowy test**
1. **🔧 System Prompt**: Ustawienie podstawowych instrukcji
2. **🎯 Stage Prompt**: Ustawienie instrukcji dla etapu
3. **💬 Wiadomość testowa**: "Cześć jestem Kacper"
4. **🔍 Test pamięci**: Sprawdzenie czy model pamięta rozmowę
5. **🎯 Test świadomości**: Czy model wie w jakim jest etapie

#### **📊 Automatyczna analiza**
- **Obsługa pamięci**: Czy model zachowuje kontekst
- **Jakość odpowiedzi**: Ocena poprawności reakcji
- **Czas odpowiedzi**: Pomiar wydajności
- **Rekomendacje**: Sugestie optymalnej konfiguracji

#### **🎯 Przykład testu**
```
System: "Jesteś profesjonalnym terapeutą TSR..."
Etap: "ETAP 1: OTWARCIE - ciepłe powitanie klienta"
Wiadomość: "Cześć jestem Kacper"
→ Odpowiedź modelu
Test pamięci: "Pokaż naszą historię rozmowy"
Test etapu: "W którym etapie terapii się znajdujemy?"
```

### Jak interpretować wyniki
- **Model z pamięcią**: Lepszy dla dłuższych sesji, niższe koszty
- **Model bez pamięci**: Wymaga więcej konfiguracji, wyższe koszty
- **Szybkie odpowiedzi**: Lepsze doświadczenie użytkownika
- **Świadomość etapu**: Ważne dla jakości terapii

## 🔧 Pliki konfiguracyjne

### Struktura konfiguracji

```
psychia/
├── .env                          # Klucze API (utwórz samodzielnie)
├── config.py                     # Główna konfiguracja Python
├── config/json/
│   ├── app_config.json          # Ustawienia aplikacji
│   └── stages/
│       └── stages.json          # Definicje etapów terapii
├── prompts/
│   ├── system/                  # Prompty systemowe
│   │   ├── therapist.yaml
│   │   └── supervisor.yaml
│   └── stages/                  # Prompty dla etapów
│       ├── therapist/           # Prompty terapeuty per etap
│       └── supervisor/          # Prompty supervisora per etap
```

### Co znajduje się w każdym pliku

#### **`.env` - Klucze API**
```bash
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
```

#### **`config/json/app_config.json` - Ustawienia aplikacji**
- Domyślne modele dla terapeuty i supervisora
- Parametry generowania (temperatura, max tokens)
- Ustawienia bezpieczeństwa
- Opcje interfejsu

#### **`config/json/stages/stages.json` - Etapy terapii**
- Definicje 5 etapów TSR
- Nazwy, opisy, kolejność
- Szacowany czas trwania każdego etapu

#### **`prompts/system/` - Prompty podstawowe**
- `therapist.yaml`: Podstawowe instrukcje dla terapeuty
- `supervisor.yaml`: Instrukcje dla supervisora

#### **`prompts/stages/` - Prompty dla etapów**
- `therapist/opening.json`: Instrukcje terapeuty dla etapu otwarcia
- `supervisor/opening.json`: Kryteria supervisora dla etapu otwarcia
- *(analogicznie dla pozostałych etapów)*

### Jak modyfikować konfigurację

1. **Zmiana modeli**: Użyj interfejsu aplikacji (pasek boczny)
2. **Zmiana parametrów**: Slider'y w aplikacji
3. **Zmiana promptów**: Edytuj pliki w `prompts/`
4. **Zmiana etapów**: Edytuj `config/json/stages/stages.json`
5. **Nowe klucze API**: Edytuj plik `.env`

---

**🧠 Psychia - Twój inteligentny asystent terapeutyczny**

*Łączy najlepsze praktyki terapii TSR z możliwościami nowoczesnej sztucznej inteligencji*