import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / 'database'
DATABASE_DIR.mkdir(exist_ok=True)

USER_FILE = DATABASE_DIR / 'users.json'
LAWYER_FILE = DATABASE_DIR / 'lawyers.json'
APPOINTMENT_FILE = DATABASE_DIR / 'appointments.json'
CURRENT_USER_FILE = DATABASE_DIR / 'current_user.json'


def _load_json(path):
    if not path.exists():
        path.write_text('[]' if path.name != 'current_user.json' else '{}', encoding='utf-8')
    with path.open('r', encoding='utf-8') as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError:
            return [] if path.name != 'current_user.json' else {}


def _save_json(path, data):
    with path.open('w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def add_user(user_data):
    users = _load_json(USER_FILE)
    users.append({
        'id': len(users) + 1,
        'created_at': datetime.utcnow().isoformat(),
        **user_data,
    })
    _save_json(USER_FILE, users)
    return users[-1]


def add_lawyer(lawyer_data):
    lawyers = _load_json(LAWYER_FILE)
    lawyers.append({
        'id': len(lawyers) + 1,
        'created_at': datetime.utcnow().isoformat(),
        **lawyer_data,
    })
    _save_json(LAWYER_FILE, lawyers)
    return lawyers[-1]


def get_all_lawyers():
    return _load_json(LAWYER_FILE)


def add_appointment(appointment_data):
    appointments = _load_json(APPOINTMENT_FILE)
    appointments.append({
        'id': len(appointments) + 1,
        'created_at': datetime.utcnow().isoformat(),
        'status': 'Pending',
        **appointment_data,
    })
    _save_json(APPOINTMENT_FILE, appointments)
    return appointments[-1]


def get_appointments_by_email(email):
    appointments = _load_json(APPOINTMENT_FILE)
    return [a for a in appointments if a.get('email', '').strip().lower() == email.strip().lower()]


def set_current_user(user_data):
    _save_json(CURRENT_USER_FILE, {
        'updated_at': datetime.utcnow().isoformat(),
        **user_data,
    })


def clear_current_user():
    _save_json(CURRENT_USER_FILE, {})


def get_current_user():
    return _load_json(CURRENT_USER_FILE)
