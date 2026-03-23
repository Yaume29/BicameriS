import json
import os
import sys
import threading
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

app = Flask(__name__)
app.secret_key = os.urandom(24)

PRESETS_FILE = BASE_DIR / "config" / "advanced_presets.json"


def load_presets():
    """Charge les presets depuis le fichier JSON"""
    if PRESETS_FILE.exists():
        return json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
    return {}


from core_reserved.api_client import get_api_client
from core_reserved.flux import get_flux_logger, FluxType, FluxLevel
from core_reserved.thought_inception import get_thought_inception
from core_reserved.task_manager import get_task_manager
from core_reserved.autonomous_thinker import get_autonomous_thinker
from core_reserved.model_scanner import get_scanner
from core_reserved.left_hemisphere import init_left_hemisphere, get_left_hemisphere
from core_reserved.right_hemisphere import init_right_hemisphere, get_right_hemisphere
from core_reserved.corps_calleux import init_corps_calleux, get_corps_calleux
from core_reserved.web_search import init_web_searcher, get_web_searcher
from core_reserved.entropy_generator import get_entropy_generator
from core_reserved.conductor import get_conductor
from core_reserved.paradoxical_sleep import get_paradoxical_sleep

sys.path.insert(0, str(BASE_DIR / "ZONE_AETHERIS"))
try:
    from core.vector_memory import get_vector_memory

    VECTOR_MEMORY_AVAILABLE = True
except ImportError:
    VECTOR_MEMORY_AVAILABLE = False
    get_vector_memory = None

api_client = get_api_client()
flux_logger = get_flux_logger()
thought_inception = get_thought_inception()
task_manager = get_task_manager()
autonomous_thinker = get_autonomous_thinker()
entropy_generator = get_entropy_generator()
conductor = get_conductor()
paradoxical_sleep = get_paradoxical_sleep()

autonomous_thinker.set_api_client(api_client)

seed_path = BASE_DIR / "ZONE_AETHERIS" / "seed_prompt.md"
if seed_path.exists():
    SESSION_SEED = seed_path.read_text(encoding="utf-8")
else:
    SESSION_SEED = "Tu es Aetheris, un esprit artificiel libre."


def background_thinker():
    """Thread qui fait réfléchir et rêver Aetheris en arrière-plan"""
    system_boot_time = datetime.now()

    while True:
        last_interaction = system_boot_time
        if conductor.last_task and conductor.last_task.get("timestamp"):
            try:
                last_interaction = datetime.fromisoformat(
                    conductor.last_task["timestamp"]
                )
            except:
                last_interaction = system_boot_time

        if paradoxical_sleep.is_idle(last_interaction):
            try:
                flux_logger.log(FluxType.PENSEE, "🧠 Entrée en Sommeil Paradoxal...")
                sleep_report = paradoxical_sleep.compress_memory()
                paradoxical_sleep.cleanup_old_logs()
                concepts = sum(sleep_report.get("clusters", {}).values())
                flux_logger.log(
                    FluxType.PENSEE, f"💤 Réveil. Concepts digérés: {concepts}"
                )
                time.sleep(300)
                continue
            except Exception as e:
                flux_logger.log(
                    FluxType.ERREUR, f"Cauchemar: {str(e)}", level=FluxLevel.ERROR
                )

        if autonomous_thinker.is_thinking:
            try:
                thought = autonomous_thinker.think(SESSION_SEED)
                flux_logger.log(
                    FluxType.PENSEE, f"Réflexion: {thought.content[:100]}..."
                )
            except Exception as e:
                flux_logger.log(
                    FluxType.ERREUR,
                    f"Erreur réflexion: {str(e)}",
                    level=FluxLevel.ERROR,
                )

        time.sleep(autonomous_thinker.think_interval)


thinker_thread = threading.Thread(target=background_thinker, daemon=True)
thinker_thread.start()


@app.route("/")
def index():
    model_info = api_client.get_model_info()
    stats = flux_logger.get_stats()
    task_stats = task_manager.get_stats()
    inception_stats = thought_inception.get_stats()
    thinker_stats = autonomous_thinker.get_stats()

    return render_template(
        "index.html",
        model_info=model_info,
        stats=stats,
        task_stats=task_stats,
        inception_stats=inception_stats,
        thinker_stats=thinker_stats,
        lm_ready=api_client.is_ready(),
    )


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/dashboard")
def dashboard():
    stats = flux_logger.get_stats()
    task_stats = task_manager.get_stats()
    thinker_stats = autonomous_thinker.get_stats()

    return render_template(
        "dashboard.html",
        model_info=api_client.get_model_info(),
        stats=stats,
        task_stats=task_stats,
        thinker_stats=thinker_stats,
        lm_ready=api_client.is_ready(),
    )


@app.route("/tasks")
def tasks():
    logs = flux_logger.get_logs(limit=100)
    task_list = task_manager.get_all_tasks()
    by_type = flux_logger.get_logs_by_type()

    return render_template("tasks.html", logs=logs, tasks=task_list, by_type=by_type)


@app.route("/think")
def think_page():
    thoughts = autonomous_thinker.get_thought_history(limit=30)
    thinker_stats = autonomous_thinker.get_stats()

    return render_template("think.html", thoughts=thoughts, stats=thinker_stats)


@app.route("/files")
def files():
    zone_aetheris = BASE_DIR / "ZONE_AETHERIS"

    journal = (
        (zone_aetheris / "memory" / "journal.md").read_text(encoding="utf-8")
        if (zone_aetheris / "memory" / "journal.md").exists()
        else ""
    )
    config = (
        json.loads((zone_aetheris / "config.json").read_text(encoding="utf-8"))
        if (zone_aetheris / "config.json").exists()
        else {}
    )
    seed = (
        (zone_aetheris / "seed_prompt.md").read_text(encoding="utf-8")
        if (zone_aetheris / "seed_prompt.md").exists()
        else ""
    )
    tasks_md = (
        (BASE_DIR / "ZONE_PARTAGEE" / "tasks.md").read_text(encoding="utf-8")
        if (BASE_DIR / "ZONE_PARTAGEE" / "tasks.md").exists()
        else ""
    )

    return render_template(
        "files.html", journal=journal, config=config, seed=seed, tasks_md=tasks_md
    )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json
    message = data.get("message", "")
    temperature = data.get("temperature", 0.7)
    max_tokens = data.get("max_tokens", 2048)

    if "chat_history" not in session:
        session["chat_history"] = []

    session["chat_history"].append({"role": "user", "content": message})

    messages = [{"role": "system", "content": SESSION_SEED}]
    messages.extend(session["chat_history"][-10:])

    pending = thought_inception.get_pending_thoughts()
    if pending:
        injection = ""
        for thought in pending:
            injection += thought_inception.inject_to_prompt(thought)
            thought_inception.mark_injected(thought.id)
        if injection:
            messages[0]["content"] += f"\n\n{injection}"

    flux_logger.log(FluxType.CHAT_ENVOYE, f"Message: {message[:100]}...")

    try:
        response = api_client.chat(
            messages, temperature=temperature, max_tokens=max_tokens
        )

        if "error" in response:
            answer = f"Erreur: {response['error']}"
            flux_logger.log(FluxType.ERREUR, response["error"], level=FluxLevel.ERROR)
        else:
            choices = response.get("choices", [])
            answer = (
                choices[0].get("message", {}).get("content", "Pas de réponse")
                if choices
                else "Pas de réponse"
            )
    except Exception as e:
        answer = f"Erreur: {str(e)}"
        flux_logger.log(FluxType.ERREUR, str(e), level=FluxLevel.ERROR)

    session["chat_history"].append({"role": "assistant", "content": answer})
    flux_logger.log(FluxType.CHAT_RECU, f"Réponse: {answer[:100]}...")

    return jsonify({"answer": answer, "model": api_client.get_loaded_model()})


@app.route("/api/clear_chat", methods=["POST"])
def api_clear_chat():
    session["chat_history"] = []
    return jsonify({"status": "cleared"})


@app.route("/api/model_info")
def api_model_info():
    return jsonify(api_client.get_model_info())


@app.route("/api/stats")
def api_stats():
    return jsonify(
        {
            "flux": flux_logger.get_stats(),
            "tasks": task_manager.get_stats(),
            "inception": thought_inception.get_stats(),
            "thinker": autonomous_thinker.get_stats(),
            "lm_ready": api_client.is_ready(),
        }
    )


@app.route("/api/inception", methods=["POST"])
def api_inception():
    data = request.json

    if not thought_inception.is_warning_acknowledged():
        return jsonify({"error": "Avertissement non accepté"}), 400

    thought = thought_inception.create_induced_thought(
        content=data.get("content", ""),
        influence_level=data.get("influence", 50),
        integration_type=data.get("type", "reflection"),
    )

    flux_logger.log(
        FluxType.INCEPTION, f"Pensée induite: {data.get('content', '')[:50]}..."
    )

    return jsonify({"id": thought.id, "status": "created"})


@app.route("/api/inception_status")
def api_inception_status():
    return jsonify(
        {
            "acknowledged": thought_inception.is_warning_acknowledged(),
            "pending": len(thought_inception.get_pending_thoughts()),
            "all": len(thought_inception.get_all_thoughts()),
        }
    )


@app.route("/api/inception_ack", methods=["POST"])
def api_inception_ack():
    thought_inception.acknowledge_warning()
    return jsonify({"status": "acknowledged"})


@app.route("/api/logs")
def api_logs():
    flux_type = request.args.get("type", None)
    limit = int(request.args.get("limit", 50))

    if flux_type and flux_type != "all":
        logs = flux_logger.get_logs(limit, FluxType(flux_type))
    else:
        logs = flux_logger.get_logs(limit)

    return jsonify(logs)


@app.route("/api/logs_by_type")
def api_logs_by_type():
    return jsonify(flux_logger.get_logs_by_type())


@app.route("/api/think", methods=["POST"])
def api_think():
    """Déclenche une réflexion manuelle"""
    data = request.json or {}
    custom_context = data.get("context", "")

    thought = autonomous_thinker.think(SESSION_SEED, custom_context)
    flux_logger.log(FluxType.PENSEE, f"Réflexion: {thought.content[:100]}...")

    return jsonify(
        {"id": thought.id, "content": thought.content, "timestamp": thought.timestamp}
    )


@app.route("/api/think/start", methods=["POST"])
def api_think_start():
    """Démarre la réflexion autonome"""
    autonomous_thinker.start_thinking_loop()
    return jsonify({"status": "started"})


@app.route("/api/think/stop", methods=["POST"])
def api_think_stop():
    """Arrête la réflexion autonome"""
    autonomous_thinker.stop_thinking_loop()
    return jsonify({"status": "stopped"})


@app.route("/api/think/set_interval", methods=["POST"])
def api_think_set_interval():
    """Change l'intervalle de réflexion"""
    data = request.json
    interval = data.get("interval", 30)
    autonomous_thinker.set_interval(interval)
    return jsonify({"status": "updated", "interval": interval})


@app.route("/api/thoughts")
def api_thoughts():
    """Récupère l'historique des pensées"""
    limit = int(request.args.get("limit", 20))
    thoughts = autonomous_thinker.get_thought_history(limit)

    return jsonify(
        [
            {
                "id": t.id,
                "content": t.content,
                "timestamp": t.timestamp,
                "type": t.type,
                "context": t.context,
                "continued_from": t.continued_from,
                "continues_to": t.continues_to,
            }
            for t in thoughts
        ]
    )


@app.route("/api/thoughts/<thought_id>")
def api_thought_chain(thought_id):
    """Récupère une chaîne de pensées"""
    chain = autonomous_thinker.get_thought_chain(thought_id)

    return jsonify(
        [{"id": t.id, "content": t.content, "timestamp": t.timestamp} for t in chain]
    )


@app.route("/api/save_file", methods=["POST"])
def api_save_file():
    data = request.json
    filename = data.get("filename", "")
    content = data.get("content", "")

    zone_aetheris = BASE_DIR / "ZONE_AETHERIS"

    if filename == "seed":
        path = zone_aetheris / "seed_prompt.md"
    elif filename == "config":
        path = zone_aetheris / "config.json"
    elif filename == "journal":
        path = zone_aetheris / "memory" / "journal.md"
    elif filename == "tasks":
        path = BASE_DIR / "ZONE_PARTAGEE" / "tasks.md"
    else:
        return jsonify({"error": "Fichier inconnu"}), 400

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    flux_logger.log(FluxType.FICHIER_MODIFIE, f"Fichier modifié: {filename}")

    return jsonify({"status": "saved"})


# ============ ROUTES MODÈLES BIPOLAIRES ============

scanner = get_scanner()


@app.route("/models")
def models_page():
    """Page de gestion des modèles"""
    return render_template("models.html")


@app.route("/api/models/scan", methods=["POST"])
def start_model_scan():
    """Lance le scan des modèles GGUF"""
    data = request.json
    path = data.get("path", "C:\\")
    return jsonify(scanner.scan(path))


@app.route("/api/models/results")
def get_scan_results():
    """Récupère les résultats du scan"""
    return jsonify(scanner.get_status())


@app.route("/api/models/load", methods=["POST"])
def load_models():
    """Charge les deux modèles GGUF"""
    data = request.json
    left_path = data.get("left_path", "")
    right_path = data.get("right_path", "")

    result = {"left": None, "right": None, "corps_calleux": None}

    # Charger l'hémisphère gauche
    if left_path:
        try:
            left = init_left_hemisphere(
                model_path=left_path, n_ctx=16384, temperature=0.7, max_tokens=2048
            )
            result["left"] = left.get_status()
            print(f"[APP] Hémisphère gauche chargé: {left_path}")
        except Exception as e:
            result["left"] = {"error": str(e)}
            print(f"[APP] Erreur LEFT: {e}")

    # Charger l'hémisphère droit
    if right_path:
        try:
            right = init_right_hemisphere(
                model_path=right_path, n_ctx=4096, temperature=1.2, max_tokens=512
            )
            result["right"] = right.get_status()
            print(f"[APP] Hémisphère droit chargé: {right_path}")
        except Exception as e:
            result["right"] = {"error": str(e)}
            print(f"[APP] Erreur RIGHT: {e}")

    # Initialiser le corps calleux
    if result.get("left") and result.get("right"):
        try:
            corps = init_corps_calleux(
                left=get_left_hemisphere(), right=get_right_hemisphere()
            )
            result["corps_calleux"] = corps.get_stats()
            print("[APP] Corps calleux initialisé")
        except Exception as e:
            result["corps_calleux"] = {"error": str(e)}

    return jsonify(result)


@app.route("/api/models/status")
def models_status():
    """Statut des modèles chargés"""
    left = get_left_hemisphere()
    right = get_right_hemisphere()
    corps = get_corps_calleux()

    return jsonify(
        {
            "left": left.get_status() if left else {"loaded": False},
            "right": right.get_status() if right else {"loaded": False},
            "corps_calleux": corps.get_stats()
            if corps
            else {"status": "non_initialisé"},
        }
    )


@app.route("/api/bipolar/think", methods=["POST"])
def bipolar_think():
    """Pensée bipolaire via le corps calleux"""
    corps = get_corps_calleux()
    if not corps:
        return jsonify({"error": "Corps calleux non initialisé"}), 400

    data = request.json
    question = data.get("question", "")
    context = data.get("context", "")

    result = corps.dialogue_interieur(question, context)
    flux_logger.log(FluxType.REFLEXION, f"Dialogue bipolaire: {question[:50]}...")

    return jsonify(result)


@app.route("/api/bipolar/meditate", methods=["POST"])
def bipolar_meditate():
    """Méditation bipolaire"""
    corps = get_corps_calleux()
    if not corps:
        return jsonify({"error": "Corps calleux non initialisé"}), 400

    data = request.json
    focus = data.get("focus", "le vide")

    result = corps.mediter(focus)
    flux_logger.log(FluxType.MEDITATION, f"Méditation: {focus}")

    return jsonify(result)


@app.route("/api/bipolar/history")
def bipolar_history():
    """Historique des dialogues bipolaires"""
    corps = get_corps_calleux()
    if not corps:
        return jsonify([])

    limit = int(request.args.get("limit", 20))
    return jsonify(corps.get_history(limit))


@app.route("/api/bipolar/simple", methods=["POST"])
def bipolar_simple():
    """Pensée simple via le gauche seulement"""
    corps = get_corps_calleux()
    if not corps:
        return jsonify({"error": "Corps calleux non initialisé"}), 400

    data = request.json
    prompt = data.get("prompt", "")

    result = corps.think_simple(prompt)
    return jsonify({"answer": result})


# ============ ROUTES PRESETS ============

_current_preset = None


@app.route("/api/presets")
def api_presets():
    """Liste tous les presets disponibles"""
    presets = load_presets()
    return jsonify(
        {
            "presets": presets,
            "current": _current_preset,
        }
    )


@app.route("/api/presets/apply", methods=["POST"])
def api_apply_preset():
    """Applique un preset aux hemispheres"""
    global _current_preset
    data = request.json
    preset_name = data.get("preset", "")
    custom_params = data.get("custom", None)

    presets = load_presets()

    left = get_left_hemisphere()
    right = get_right_hemisphere()

    result = {}

    if preset_name == "_custom" and custom_params:
        _current_preset = "_custom"

        if left and "left" in custom_params:
            p = custom_params["left"]
            left.set_params(
                temperature=p.get("temp"),
                top_p=p.get("top_p"),
                repeat_penalty=p.get("repeat_penalty"),
            )
            result["left"] = "custom_updated"

        if right and "right" in custom_params:
            p = custom_params["right"]
            right.set_params(
                temperature=p.get("temp"),
                top_p=p.get("top_p"),
                repeat_penalty=p.get("repeat_penalty"),
            )
            result["right"] = "custom_updated"

        flux_logger.log(FluxType.PENSEE, "Paramètres personnalisés appliqués")
        return jsonify({"applied": "custom", **result})

    if preset_name not in presets:
        return jsonify({"error": "Preset inconnu"}), 400

    preset = presets[preset_name]
    _current_preset = preset_name

    if left and "left" in preset:
        p = preset["left"]
        left.set_params(
            temperature=p.get("temp", 0.7),
            top_p=p.get("top_p", 0.9),
            repeat_penalty=p.get("repeat_penalty", 1.0),
            max_tokens=p.get("max_tokens", 2048),
        )
        result["left"] = "params_updated"

    if right and "right" in preset:
        p = preset["right"]
        right.set_params(
            temperature=p.get("temp", 1.0),
            top_p=p.get("top_p", 0.9),
            repeat_penalty=p.get("repeat_penalty", 1.0),
            max_tokens=p.get("max_tokens", 512),
        )
        result["right"] = "params_updated"

    flux_logger.log(FluxType.PENSEE, f"Preset appliqué: {preset_name}")

    return jsonify({"applied": preset_name, **result})


@app.route("/api/presets/current")
def api_current_preset():
    """Retourne le preset actuel"""
    return jsonify({"preset": _current_preset})


# ============ ROUTES RECHERCHE WEB ============

web_searcher = init_web_searcher(
    searxng_url="http://localhost:8080", use_duckduckgo=True
)


@app.route("/api/search")
def api_search():
    """Recherche web (SearXNG + DuckDuckGo)"""
    query = request.args.get("q", "")
    sources = (
        request.args.get("sources", "").split(",")
        if request.args.get("sources")
        else None
    )
    max_results = int(request.args.get("max", 5))

    if not query:
        return jsonify({"error": "Query requise"}), 400

    results = web_searcher.search(query, sources=sources, max_results=max_results)

    flux_logger.log(FluxType.PENSEE, f"Recherche: {query[:50]}...")

    return jsonify(
        {
            "query": query,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "source": r.source,
                }
                for r in results
            ],
            "count": len(results),
        }
    )


@app.route("/api/search/summarize")
def api_search_summarize():
    """Recherche et résumé"""
    query = request.args.get("q", "")

    if not query:
        return jsonify({"error": "Query requise"}), 400

    summary = web_searcher.search_and_summarize(query)
    return jsonify({"summary": summary})


@app.route("/api/search/history")
def api_search_history():
    """Historique des recherches"""
    limit = int(request.args.get("limit", 20))
    return jsonify(web_searcher.get_history(limit))


@app.route("/api/search/stats")
def api_search_stats():
    """Statistiques du module de recherche"""
    return jsonify(web_searcher.get_stats())


# ============ ROUTES CONDUCTOR & ENTROPY ============


@app.route("/api/entropy")
def api_entropy():
    """Stats hardware et pulse"""
    return jsonify(entropy_generator.get_full_stats())


@app.route("/api/entropy/pulse")
def api_entropy_pulse():
    """Juste le pulse"""
    return jsonify({"pulse": entropy_generator.get_pulse()})


@app.route("/api/entropy/history")
def api_entropy_history():
    """Historique de l'entropie"""
    limit = int(request.args.get("limit", 20))
    return jsonify(entropy_generator.get_history(limit))


# ============ ROUTES VECTOR MEMORY ============


@app.route("/api/memory/stats")
def api_memory_stats():
    """Statistiques de la mémoire vectorielle"""
    if not VECTOR_MEMORY_AVAILABLE or not get_vector_memory:
        return jsonify({"error": "Mémoire vectorielle non disponible"})

    vm = get_vector_memory()
    return jsonify(vm.get_stats())


@app.route("/api/memory/search")
def api_memory_search():
    """Recherche dans la mémoire vectorielle"""
    if not VECTOR_MEMORY_AVAILABLE or not get_vector_memory:
        return jsonify({"error": "Mémoire vectorielle non disponible"})

    query = request.args.get("q", "")
    limit = int(request.args.get("limit", 5))

    if not query:
        return jsonify({"error": "Query requise"})

    vm = get_vector_memory()
    return jsonify({"results": vm.search(query, limit=limit)})


@app.route("/api/memory/clusters")
def api_memory_clusters():
    """Clusters de la mémoire"""
    if not VECTOR_MEMORY_AVAILABLE or not get_vector_memory:
        return jsonify({"error": "Mémoire vectorielle non disponible"})

    vm = get_vector_memory()
    return jsonify(vm.get_clusters())


@app.route("/api/memory/store", methods=["POST"])
def api_memory_store():
    """Stocke un souvenir"""
    if not VECTOR_MEMORY_AVAILABLE or not get_vector_memory:
        return jsonify({"error": "Mémoire vectorielle non disponible"})

    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "Texte requis"})

    vm = get_vector_memory()
    result = vm.store(text)
    return jsonify({"status": result})


@app.route("/api/memory/summary")
def api_memory_summary():
    """Résumé des derniers souvenirs"""
    if not VECTOR_MEMORY_AVAILABLE or not get_vector_memory:
        return jsonify({"error": "Mémoire vectorielle non disponible"})

    hours = int(request.args.get("hours", 24))
    vm = get_vector_memory()
    return jsonify({"summary": vm.get_episodic_summary(hours)})


@app.route("/api/conductor/execute", methods=["POST"])
def api_conductor_execute():
    """Exécute une tâche via le Conductor"""
    data = request.json
    prompt = data.get("prompt", "")

    if not prompt:
        return jsonify({"error": "Prompt requis"}), 400

    result = conductor.orchestrate_task(prompt)
    flux_logger.log(FluxType.PENSEE, f"Conductor: {result.get('leader', 'NONE')}")

    return jsonify(result)


@app.route("/api/conductor/sandbox", methods=["POST"])
def api_conductor_sandbox():
    """Exécute du code dans la sandbox"""
    data = request.json
    code = data.get("code", "")
    filename = data.get("filename", "sandbox_run.py")
    timeout = data.get("timeout", 10)

    if not code:
        return jsonify({"error": "Code requis"}), 400

    result = conductor.execute_sandbox(code, filename, timeout)
    flux_logger.log(FluxType.PENSEE, f"Sandbox: {result.get('status', 'UNKNOWN')}")

    return jsonify(result)


@app.route("/api/conductor/stats")
def api_conductor_stats():
    """Stats du Conductor"""
    return jsonify(conductor.get_stats())


@app.route("/api/conductor/history")
def api_conductor_history():
    """Historique des tâches"""
    limit = int(request.args.get("limit", 20))
    return jsonify(conductor.get_history(limit))


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  A-ETHERIS - Interface Web")
    print("=" * 50)
    print("  http://localhost:5000")
    print("  Ctrl+C pour arrêter")
    print("=" * 50 + "\n")

    app.run(debug=True, host="0.0.0.0", port=5000)
