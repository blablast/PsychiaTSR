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
- [🧪 Testowanie modeli](#-testowanie-modeli)
- [🔧 Rozwój](#-rozwój)
- [📁 Struktura projektu](#-struktura-projektu)
- [🤝 Współpraca](#-współpraca)

## 🎯 Cel projektu

Psychia to zaawansowany asystent terapeutyczny wykorzystujący **Solution-Focused Brief Therapy (TSR)** - metodę terapii skupioną na rozwiązaniach zamiast problemach. System oferuje:

- **Profesjonalną terapię TSR** z wykorzystaniem AI
- **Dwuagentowy system** z supervisorem i terapeutą
- **Protokoły bezpieczeństwa** dla sytuacji kryzysowych
- **Elastyczną architekturę** obsługującą różne modele LLM
- **Zaawansowaną strategię pamięci** prompt'ów systemowych i etapowych

## ✨ Funkcjonalności

### 🎭 **Dwuagentowy System AI**
- **🩺 Terapeuta**: Prowadzi rozmowę terapeutyczną według zasad TSR
- **👥 Supervisor**: Ocenia postępy i zarządza przejściami między etapami
- **🧠 BaseAgent**: Inteligentna obsługa pamięci konwersacji i prompt'ów
- **⚡ Memory Optimization**: 3-poziomowy system optymalizacji pamięci

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
- **🌐 OpenAI** (GPT-4o, GPT-4o-mini, GPT-4, GPT-3.5-turbo)
- **🧠 Google Gemini** (gemini-1.5-flash, gemini-1.5-pro, gemini-pro)
- **🔍 Dynamiczne wykrywanie** modeli z cache JSON
- **🔄 ModelDiscovery** - automatyczne refreshowanie z 7-dniowym cache

### 🧪 **Advanced Model Testing**
- **💬 Chat Mode**: Prosty interfejs testowania modeli
- **🧠 Memory Test Mode**: Kompleksowe testowanie pamięci prompt'ów
- **📊 5-stopniowy test**: System → Stage → Conversation → Memory → Awareness
- **🔬 Analiza wyników**: Automatyczna ocena możliwości modelu

### 🔧 **Zaawansowane Logowanie**
- **📝 Logi techniczne** z pełną historią konwersacji
- **📋 Kopiowanie bloków** logów według interakcji użytkownika
- **🎯 Wskaźniki zmian etapów** w czasie rzeczywistym
- **🔍 Pełne prompty** w rozwijaných kontenerach

## 🏗️ Architektura SOLID

Projekt ściśle przestrzega zasad **SOLID** z zaawansowanym systemem zarządzania pamięcią:

### **S** - Single Responsibility Principle
```python
class BaseAgent:                # Wspólna logika dla wszystkich agentów
class TherapistAgent(BaseAgent): # Tylko interakcja terapeutyczna
class SupervisorAgent(BaseAgent): # Tylko ocena etapów
class StagePromptManager:       # Tylko zarządzanie promptami etapów
class SystemPromptManager:      # Tylko zarządzanie promptami systemowych
class UnifiedPromptManager:     # Orkiestracja prompt'ów
```

### **O** - Open/Closed Principle
```python
# Łatwe dodawanie nowych implementacji
class NewLLMProvider(LLMProvider): ...
class NewAgent(BaseAgent): ...
```

### **L** - Liskov Substitution Principle
```python
# Wszystkie implementacje są zamienne
provider: LLMProvider = OpenAIProvider()
provider: LLMProvider = GeminiProvider()
agent: BaseAgent = TherapistAgent()
agent: BaseAgent = SupervisorAgent()
```

### **I** - Interface Segregation Principle
```python
# Małe, specjalizowane interfejsy
class IAgentProvider: ...        # Tylko zarządzanie agentami
class ISessionState: ...         # Tylko stan sesji
class ITechnicalLogger: ...      # Tylko logowanie techniczne
```

### **D** - Dependency Inversion Principle
```python
# Zależności od abstrakcji, nie konkretnych klas
class BaseAgent:
    def __init__(self, llm_provider: LLMProvider, safety_checker: SafetyChecker):
```

## 🚀 Instalacja

### Wymagania systemowe
- **Python 3.12+**
- **4GB RAM** minimum (dla modeli chmurowych)
- **16GB+ RAM** zalecane dla lokalnych modeli

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
# OpenAI (zalecane)
OPENAI_API_KEY=sk-your-api-key-here
DEFAULT_THERAPIST_MODEL=gpt-4o-mini
DEFAULT_SUPERVISOR_MODEL=gpt-4o-mini

# Google Gemini (opcjonalnie)
GOOGLE_API_KEY=your-gemini-api-key

# Bezpieczeństwo
ENABLE_SAFETY_CHECKS=true
STRICT_SAFETY_MODE=false

# ModelDiscovery
MODEL_CACHE_TTL_DAYS=7  # Cache modeli przez 7 dni
```

## 💻 Użycie

### Szybki start

1. **Uruchom aplikację**:
   ```bash
   streamlit run app.py
   ```

2. **Skonfiguruj modele** w pasku bocznym:
   - Wprowadź klucze API
   - Wybierz modele dla terapeuty i supervisora z dynamicznej listy
   - System automatycznie pobierze aktualne modele z API

3. **Rozpocznij terapię**: Napisz pierwszą wiadomość

### Interfejs użytkownika

#### Panel główny
- **💬 Okno czatu**: Główna przestrzeń rozmowy z informacją o aktualnym etapie
- **🎯 Kontrola etapów**: Nawigacja między etapami terapii
- **🔧 Logi techniczne**: Szczegółowe logi z kopiowaniem bloków

#### Funkcje logów
- **📋 Kopiowanie bloków**: Każdy blok interakcji można skopiować osobno
- **🔍 Rozwijane prompty**: Pełne prompty w kontenerach podobnych do JSON
- **🎯 Wskaźniki etapów**: Jasne sygnalizowanie zmian etapów
- **📊 Pełna historia**: Bez limitów - wszystkie wiadomości są zachowane

## 🤖 Modele LLM

### Dynamiczne wykrywanie modeli

System wykorzystuje **ModelDiscovery** z JSON cache:
- **Automatyczne refresh**: Co 7 dni lub na żądanie
- **API fallback**: Bezpośrednie połączenie gdy cache niedostępny
- **Smart caching**: Lokalne przechowywanie przez określony czas

### Zalecane konfiguracje

#### **🏆 Konfiguracja Idealna** (chmurowa)
- **Terapeuta**: `gpt-4o` - najlepsza jakość konwersacji
- **Supervisor**: `gpt-4o-mini` - ekonomiczna ocena etapów
- **Wymagania**: Klucze API OpenAI
- **Zalety**: Najnowsze możliwości, niskie koszty

#### **⚡ Konfiguracja Budżetowa** (chmurowa)
- **Terapeuta**: `gpt-4o-mini`
- **Supervisor**: `gpt-4o-mini`
- **Wymagania**: Klucz API OpenAI
- **Zalety**: Bardzo niskie koszty, dobra jakość

#### **🧠 Konfiguracja Gemini**
- **Terapeuta**: `gemini-1.5-pro`
- **Supervisor**: `gemini-1.5-flash`
- **Wymagania**: Klucz API Google
- **Zalety**: Alternatywa dla OpenAI, długi kontekst

### Status modeli
System automatycznie wykrywa dostępne modele:
- ✅ **Gotowy**: Model dostępny do użycia
- ⚠️ **Wymaga klucza API**: Model chmurowy bez konfiguracji
- ❌ **Niedostępny**: Model nie jest dostępny

## 🧪 Testowanie modeli

### Memory Test Mode

Aplikacja zawiera zaawansowany system testowania pamięci modeli:

#### **🔬 5-stopniowy test pamięci:**
1. **🔧 System Prompt**: Ustawienie globalnych instrukcji
2. **🎯 Stage Prompt**: Ustawienie instrukcji etapu
3. **💬 Test Message**: Wysłanie testowej wiadomości
4. **🔍 Memory Check**: Sprawdzenie historii konwersacji
5. **🎯 Stage Awareness**: Weryfikacja świadomości etapu

#### **📊 Analiza automatyczna:**
- **Memory Support**: Czy model wspiera pamięć konwersacji
- **Prompt Strategy**: Optymalna strategia dla danego modelu
- **Performance Metrics**: Czas odpowiedzi i jakość
- **Recommendations**: Zalecenia konfiguracji

#### **🎯 Test scenariusze:**
```
System: "Jesteś profesjonalnym terapeutą..."
Stage: "ETAP 1: POWITANIE - ciepłe powitanie klienta"
Message: "Cześć jestem Kacper"
→ Model Response
Memory Check: "Pokaż naszą historię bez promptów"
Stage Check: "W którym etapie się znajdujemy?"
```

## 🔧 Rozwój

### Dodanie nowego providera LLM

```python
# 1. Utwórz provider w llm/
class CustomLLMProvider(LLMProvider):
    def generate_sync(self, prompt: str, **kwargs):
        # Implementacja z obsługą pamięci konwersacji
        pass

    # Implementuj metody pamięci jeśli wspierane
    def set_system_prompt(self, prompt: str): ...
    def add_user_message(self, message: str): ...
    def add_assistant_message(self, message: str): ...

# 2. Dodaj do model_discovery.py
async def get_custom_models():
    return [{"id": "model-1", "name": "Custom Model 1", "available": True}]
```

### Dodanie nowego agenta

```python
# Nowy agent dziedziczy z BaseAgent
class CustomAgent(BaseAgent):
    def generate_response(self, *args, **kwargs) -> Dict[str, Any]:
        # Implementacja specjalizowanej logiki
        # BaseAgent automatycznie obsługuje pamięć
        return {"success": True, "response": "..."}
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

# 2. Utwórz prompty w prompts/stages/therapist/new_stage.json
# 3. Utwórz prompty w prompts/stages/supervisor/new_stage.json
```

## 📁 Struktura projektu

```
psychia/
├── 📁 src/
│   ├── 📁 agents/                    # Agenci AI
│   │   ├── base.py                   # BaseAgent - wspólna logika
│   │   ├── therapist.py             # Agent terapeuty z memory optimization
│   │   └── supervisor.py            # Agent supervisora z stage memory
│   ├── 📁 core/                     # Logika biznesowa
│   │   ├── 📁 prompts/              # Zarządzanie promptami
│   │   │   ├── stage_prompt_manager.py      # Prompty etapów
│   │   │   ├── system_prompt_manager.py     # Prompty systemowe
│   │   │   └── unified_prompt_manager.py    # Orkiestracja
│   │   ├── 📁 workflow/             # Workflow management
│   │   │   ├── therapist_responder.py      # Logic terapeuty
│   │   │   └── supervisor_evaluator.py     # Logic supervisora
│   │   ├── 📁 session/              # Zarządzanie sesją
│   │   └── therapy_workflow_manager.py     # Główny orkiestrator
│   ├── 📁 llm/                      # Providery LLM
│   │   ├── base.py                  # BaseProvider z memory support
│   │   ├── openai_provider.py       # OpenAI z conversation memory
│   │   ├── gemini_provider.py       # Gemini z session memory
│   │   └── model_discovery.py       # Dynamiczne wykrywanie z cache
│   ├── 📁 ui/                       # Interfejs użytkownika
│   │   ├── 📁 pages/               # Strony Streamlit
│   │   │   ├── therapy.py          # Główna strona terapii
│   │   │   ├── model_test.py       # Zaawansowane testowanie modeli
│   │   │   ├── prompts.py          # Zarządzanie promptami
│   │   │   └── testing.py          # Narzędzia deweloperskie
│   │   ├── chat.py                 # Interfejs czatu
│   │   ├── technical_log_display.py    # Wyświetlanie logów
│   │   └── sidebar.py              # Konfiguracja w pasku bocznym
│   └── 📁 utils/                    # Narzędzia pomocnicze
├── 📁 prompts/                      # Prompty systemowe
│   ├── 📁 stages/                  # Prompty etapów (nowy format TSR)
│   │   ├── 📁 therapist/           # Prompty terapeuty per etap
│   │   └── 📁 supervisor/          # Prompty supervisora per etap
│   └── 📁 system/                  # Prompty systemowe
├── 📁 stages/                       # Konfiguracja etapów TSR
├── app.py                          # Główny plik aplikacji
├── config.py                       # Konfiguracja systemowa
└── requirements.txt                # Zależności Python
```

## 🚀 Funkcjonalności Zaawansowane

### 🧠 **Smart Memory Management**
- **3-poziomowy system**: Ultra-optimized → Memory-optimized → Traditional
- **Automatyczna detekcja**: System wykrywa możliwości provider'a
- **Stage Memory**: Inteligentne zarządzanie promptami etapów
- **Memory Info**: Debugowanie i monitoring stanu pamięci

### 🔧 **System Logowania**
- **Pełna historia**: Wszystkie konwersacje bez limitów
- **Bloki interakcji**: Logowanie grupowane według wiadomości użytkownika
- **Kopiowanie**: Każdy blok można skopiować do schowka
- **Prompty**: Pełne prompty w rozwijaných kontenerach
- **Wizualne wskaźniki**: Różne kolory dla różnych typów logów

### 🎯 **Zarządzanie Etapami**
- **Automatyczna progresja**: Supervisor decyduje o przejściach
- **Manualna kontrola**: Możliwość ręcznej zmiany etapów
- **Unified Stage Memory**: Supervisor pamięta kontekst etapu
- **Stage Prompt Optimization**: Wysyłanie prompt'ów etapu tylko raz

### 🛡️ **Bezpieczeństwo**
- **Detekcja kryzysów**: Automatyczne wykrywanie ryzyka
- **Protokół kryzysowy**: Natychmiastowe uruchomienie procedur bezpieczeństwa
- **Numery alarmowe**: Telefon Zaufania, Pogotowie Ratunkowe
- **Izolacja danych**: Każdy agent ma dedykowaną sesję

### 🧪 **Advanced Testing Framework**
- **Memory Testing**: Kompleksowe testowanie pamięci prompt'ów
- **Model Comparison**: Porównywanie różnych modeli i provider'ów
- **Performance Analysis**: Metryki czasu odpowiedzi i jakości
- **Configuration Recommendations**: Automatyczne zalecenia konfiguracji

---

**🧠 Psychia - Inteligentne wsparcie terapeutyczne z zaawansowaną architekturą AI**

*Developed with ❤️ using SOLID principles and cutting-edge AI memory optimization*