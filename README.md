# Inzira y'ubugingo

Django site for gospel teaching resources, Q&A, and pastor contact via WhatsApp.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_site
python manage.py createsuperuser
python manage.py populate_dummy   # optional sample data
```

To reset and reload demo content:

```bash
python manage.py populate_dummy --clear
```

## Roles

| Role | Access |
|------|--------|
| **Superuser / staff** | Django admin (`/admin/`), dashboard, contact messages, all content |
| **Pastor** | Dashboard: post resources (sermons, PDFs, slides), answer questions |

Add a user to the Pastor group:

```bash
python manage.py setup_site --create-pastor username
```

Pastors also need `is_staff` only if they should manage Get in Touch messages in the dashboard; otherwise assign the **Pastor** group only.

## Dashboard URLs

- Staff login: `/dashboard/login/`
- Overview: `/dashboard/`
- Django admin (full CMS): `/admin/`

## Dynamic content

Edit **Content blocks** in Django admin (keys: `hero_title`, `hero_subtitle`, `stat_sermons`, `featured_youtube`, etc.).

## Get in Touch & WhatsApp

New contact form submissions create a dashboard notification and a pre-filled WhatsApp link to **0783558316** (configurable via `ADMIN_WHATSAPP_NUMBER` in `.env`).

Automatic WhatsApp API delivery requires a business API (Twilio, Meta Cloud API); this project uses click-to-chat links.

## Languages (English & Kinyarwanda)

Visitors choose **English** or **Kinyarwanda** from the language dropdown in the navbar. The choice is saved in the session.

After editing translations in `locale/rw/LC_MESSAGES/django.po`, recompile:

```bash
pip install babel
python -c "from babel.messages.pofile import read_po; from babel.messages.mofile import write_mo; po=read_po(open('locale/rw/LC_MESSAGES/django.po','rb')); write_mo(open('locale/rw/LC_MESSAGES/django.mo','wb'), po)"
```

Or install [GNU gettext](https://www.gnu.org/software/gettext/) and run `python manage.py compilemessages`.

## Public features

- `/qa/` — ask questions; public answers when marked visible
- `/get-in-touch/` — contact the pastor (full name, optional email, WhatsApp phone)
- `/youtube/`, `/audio/`, `/pdf-content/`, `/slides/` — resource listings
