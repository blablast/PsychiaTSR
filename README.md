# 🧠 Psychia - Asystent Terapii TSR

**Zaawansowany system terapii Solution-Focused Brief Therapy (TSR) z wykorzystaniem sztucznej inteligencji**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39+-red.svg)](https://streamlit.io)
[![Architecture](https://img.shields.io/badge/Architecture-SOLID-green.svg)](#architektura-solid)

## 📋 Spis treści

- [🎯 Cel projektu](#-cel-projektu)
- [✨ Funkcjonalności](#-funkcjonalności)
- [🏗️ Architektura SOLID](#️-architektura-solid)
- [🚀 Instalacja](#-instalacja)
- [⚙️ Konfiguracja](#️-konfiguracja)
- [💻 Użycie](#-użycie)
- [🤖 Modele LLM](#-modele-llm)
- [🔧 Rozwój](#-rozwój)
- [📁 Struktura projektu](#-struktura-projektu)
- [🤝 Współpraca](#-współpraca)

## 🎯 Cel projektu

Psychia to zaawansowany asystent terapeutyczny wykorzystujący **Solution-Focused Brief Therapy (TSR)** - metodę terapii skupioną na rozwiązaniach zamiast problemach. System oferuje:

- **Profesjonalną terapię TSR** z wykorzystaniem AI
- **Dwuagentowy system** z supervisorem i terapeutą
- **Protokoły bezpieczeństwa** dla sytuacji kryzysowych
- **Elastyczną architekturę** obsługującą różne modele LLM

## ✨ Funkcjonalności

### 🎭 **Dwuagentowy System AI**
- **🩺 Terapeuta**: Prowadzi rozmowę terapeutyczną według zasad TSR
- **👥 Supervisor**: Ocenia postępy i zarządza przejściami między etapami
- **🔒 Izolacja sesji**: Każdy agent ma dedykowaną sesję dla lepszej wydajności

### 📋 **Etapy Terapii TSR**
1. **🤝 Powitanie i Kontrakt** - Nawiązanie kontaktu i ustalenie celów
2. **🎯 Formułowanie Celów** - Precyzyjne określenie pożądanych zmian
3. **✨ Pytanie o Cud** - Wizualizacja idealnej przyszłości
4. **💎 Pytania Wyjątkowe** - Odkrywanie istniejących zasobów
5. **📊 Pytania Skalujące** - Ocena postępów (1-10)
6. **📋 Planowanie Działań** - Konkretne kroki do realizacji
7. **🎊 Zamknięcie** - Podsumowanie i motywacja

### 🚨 **Protokoły Bezpieczeństwa**
- **Automatyczna detekcja** ryzyka samobójczego
- **Protokół kryzysowy** z numerami alarmowymi
- **Zawsze aktywne** monitorowanie bezpieczeństwa

### 🤖 **Obsługa Wielu Providerów LLM**
- **🖥️ Ollama** (lokalne modele - zalecane)
- **🌐 OpenAI** (GPT-4o, GPT-4o-mini)
- **🧠 Google Gemini** (gemini-pro)
- **🔍 Automatyczne wykrywanie** dostępnych modeli

### 🔧 **Zaawansowane Logowanie**
- **📝 Logi techniczne** z pełną historią konwersacji
- **📋 Kopiowanie bloków** logów według interakcji użytkownika
- **🎯 Wskaźniki zmian etapów** w czasie rzeczywistym
- **🔍 Pełne prompty** w rozwijaných kontenerach

## 🏗️ Architektura SOLID

Projekt ściśle przestrzega zasad **SOLID**:

### **S** - Single Responsibility Principle
```python
class TherapistAgent:           # Tylko interakcja terapeutyczna
class SupervisorAgent:          # Tylko ocena etapów
class PromptManager:            # Tylko zarządzanie promptami
class SessionManager:           # Tylko zarządzanie sesją
```

### **O** - Open/Closed Principle
```python
# Łatwe dodawanie nowych implementacji
class NewLLMProvider(LLMProvider): ...
class NewStorageBackend(ILogStorage): ...
```

### **L** - Liskov Substitution Principle
```python
# Wszystkie implementacje są zamienne
provider: LLMProvider = OllamaProvider()
provider: LLMProvider = OpenAIProvider()
```

### **I** - Interface Segregation Principle
```python
# Małe, specjalizowane interfejsy
class ILogStorage: ...           # Tylko storage
class IAgentProvider: ...        # Tylko zarządzanie agentami
class ISessionState: ...         # Tylko stan sesji
```

### **D** - Dependency Inversion Principle
```python
# Zależności od abstrakcji, nie konkretnych klas
class TherapyWorkflowManager:
    def __init__(self, agent_provider: IAgentProvider, session_manager: SessionManager):
```

## 🚀 Instalacja

### Wymagania systemowe
- **Python 3.12+**
- **Ollama** (zalecane, dla lokalnych modeli)
- **4GB RAM** minimum (16GB+ zalecane dla lokalnych modeli)

### Szybka instalacja

```bash
# Klonowanie repozytorium
git clone https://github.com/your-username/psychia.git
cd psychia

# Tworzenie środowiska wirtualnego
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalacja zależności
pip install -r requirements.txt

# Uruchomienie
streamlit run app.py
```

## ⚙️ Konfiguracja

### Zmienne środowiskowe

Utwórz plik `.env`:

```bash
# Ollama (zalecane)
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_THERAPIST_MODEL=gemma3:27b
DEFAULT_SUPERVISOR_MODEL=SpeakLeash/bielik-11b-v2.3-instruct:Q6_K

# OpenAI (opcjonalnie)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Google Gemini (opcjonalnie)
GOOGLE_API_KEY=your-gemini-api-key

# Bezpieczeństwo
ENABLE_SAFETY_CHECKS=true
STRICT_SAFETY_MODE=false
```

## 💻 Użycie

### Szybki start

1. **Uruchom aplikację**:
   ```bash
   streamlit run app.py
   ```

2. **Skonfiguruj modele** w pasku bocznym:
   - Wprowadź klucze API (jeśli używasz modeli chmurowych)
   - Kliknij "🔄 Odśwież listę modeli"
   - Wybierz modele dla terapeuty i supervisora

3. **Rozpocznij terapię**: Napisz pierwszą wiadomość

### Interfejs użytkownika

#### Panel główny
- **💬 Okno czatu**: Główna przestrzeń rozmowy z informacją o aktualnym etapie
- **🎯 Kontrola etapów**: Nawigacja między etapami terapii (pod chatem)
- **🔧 Logi techniczne**: Szczegółowe logi z kopiowaniem bloków

#### Funkcje logów
- **📋 Kopiowanie bloków**: Każdy blok interakcji można skopiować osobno
- **🔍 Rozwijane prompty**: Pełne prompty w kontenerach podobnych do JSON
- **🎯 Wskaźniki etapów**: Jasne sygnalizowanie zmian etapów
- **📊 Pełna historia**: Bez limitów - wszystkie wiadomości są zachowane

## 🤖 Modele LLM

### Zalecane konfiguracje

#### **🏆 Konfiguracja Idealna** (lokalna)
- **Terapeuta**: `gemma3:27b` - najlepsza jakość konwersacji
- **Supervisor**: `SpeakLeash/bielik-11b-v2.3-instruct:Q6_K` - polski model oceny
- **Wymagania**: 24GB+ RAM
- **Zalety**: Prywatność, brak kosztów, polski język

#### **⚡ Konfiguracja Lekka** (lokalna)
- **Terapeuta**: `llama3.1:8b`
- **Supervisor**: `gemma3:9b`
- **Wymagania**: 12GB+ RAM
- **Zalety**: Mniejsze wymagania sprzętowe

#### **☁️ Konfiguracja Chmurowa**
- **Terapeuta**: `gpt-4o-mini`
- **Supervisor**: `gpt-4o-mini`
- **Wymagania**: Klucze API, połączenie internetowe
- **Zalety**: Brak wymagań lokalnych, najnowsze możliwości

### Status modeli
System automatycznie wykrywa dostępne modele:
- ✅ **Gotowy**: Model dostępny do użycia
- ⚠️ **Wymaga klucza API**: Model chmurowy bez konfiguracji
- ❌ **Niedostępny**: Model nie jest zainstalowany

## 🔧 Rozwój

### Dodanie nowego providera LLM

```python
# 1. Utwórz provider w llm/
class CustomLLMProvider(LLMProvider):
    def generate_sync(self, prompt: str, **kwargs):
        # Implementacja
        pass

# 2. Dodaj do model_discovery.py
def get_custom_models():
    return [{"id": "model-1", "name": "Custom Model 1", "available": True}]
```

### Dodanie nowego etapu terapii

```python
# 1. Dodaj definicję etapu w stages/stages.json
{
    "id": "new_stage",
    "name": "Nowy Etap",
    "order": 8,
    "criteria": {...}
}

# 2. Utwórz prompty w prompts/supervisor/new_stage.json
# 3. Utwórz prompty w prompts/therapist/new_stage.json
```

## 📁 Struktura projektu

```
psychia/
├── 📁 agents/                    # Agenci AI
│   ├── therapist.py             # Agent terapeuty (business logic)
│   └── supervisor.py            # Agent supervisora (evaluation)
├── 📁 core/                     # Logika biznesowa
│   ├── 📁 exceptions/           # Wyjątki systemowe
│   ├── 📁 interfaces/           # Abstrakcje (SOLID)
│   ├── 📁 models/              # Modele danych
│   ├── 📁 storage/             # Implementacje storage
│   ├── therapy_workflow_manager.py  # Główny orkiestrator
│   ├── session_manager_main.py      # Zarządzanie sesją
│   ├── supervisor_evaluator.py      # Ewaluacja supervisora
│   ├── therapist_responder.py       # Odpowiedzi terapeuty
│   └── prompt_manager.py            # Zarządzanie promptami
├── 📁 llm/                     # Providery LLM
│   ├── openai_provider.py      # OpenAI integration
│   ├── gemini_provider.py      # Google Gemini
│   └── model_discovery.py      # Wykrywanie modeli
├── 📁 ui/                      # Interfejs użytkownika
│   ├── 📁 pages/              # Strony Streamlit
│   ├── chat.py                # Interfejs czatu
│   ├── technical_log_display.py    # Wyświetlanie logów
│   └── sidebar.py             # Pasek boczny
├── 📁 prompts/                 # Prompty systemowe
│   ├── 📁 therapist/          # Prompty terapeuty
│   └── 📁 supervisor/         # Prompty supervisora
├── 📁 data/                    # Dane aplikacji
│   ├── 📁 sessions/           # Zapisane sesje JSON
│   └── 📁 logs/              # Szczegółowe logi agentów
├── 📁 stages/                  # Konfiguracja etapów TSR
├── app.py                      # Główny plik aplikacji
├── config.py                   # Konfiguracja systemowa
└── requirements.txt            # Zależności Python
```

## 🚀 Funkcjonalności Zaawansowane

### 🔧 System Logowania
- **Pełna historia**: Wszystkie konwersacje bez limitów
- **Bloki interakcji**: Logowanie grupowane według wiadomości użytkownika
- **Kopiowanie**: Każdy blok można skopiować do schowka
- **Prompty**: Pełne prompty w rozwijaných kontenerach
- **Wizualne wskaźniki**: Różne kolory dla różnych typów logów

### 🎯 Zarządzanie Etapami
- **Automatyczna progresja**: Supervisor decyduje o przejściach
- **Manualna kontrola**: Możliwość ręcznej zmiany etapów
- **Wizualne wskaźniki**: Jasne sygnalizowanie zmian w czacie i logach
- **Powrót do poprzednich**: Możliwość cofania się między etapami

### 🛡️ Bezpieczeństwo
- **Detekcja kryzysów**: Automatyczne wykrywanie ryzyka
- **Protokół kryzysowy**: Natychmiastowe uruchomienie procedur bezpieczeństwa
- **Numery alarmowe**: Telefon Zaufania, Pogotowie Ratunkowe
- **Izolacja danych**: Każdy agent ma dedykowaną sesję

---

**🧠 Psychia - Inteligentne wsparcie terapeutyczne dla każdego**

*Developed with ❤️ 