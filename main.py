import streamlit as st
from pathlib import Path
import json
import uuid
import base64
import requests

# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="Nav Durga Utsav Samiti",
    page_icon="🙏",
    layout="wide"
)

# =========================================================
# FOLDERS
# =========================================================

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
GALLERY_DIR = ASSETS_DIR / "gallery"
DATA_DIR = BASE_DIR / "data"

ASSETS_DIR.mkdir(exist_ok=True)
GALLERY_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# =========================================================
# FILES
# =========================================================

CONTENT_FILE = DATA_DIR / "content.json"
AARTI_FILE = DATA_DIR / "aarti.json"
ACCOUNT_FILE = DATA_DIR / "accounts.json"
PROGRAMS_FILE = DATA_DIR / "programs.json"

ADMIN_PASSWORD = "HIMANSHU@786"

# =========================================================
# DEFAULT WEBSITE DATA
# =========================================================

DEFAULT_CONTENT = {
    "committee_name": "नव दुर्गा उत्सव समिति",
    "location": "New Salaiya",
    "tagline": "भक्ति, एकता और सेवा का उत्सव",

    "home_title": "जय माता दी 🙏",
    "home_text": "नव दुर्गा उत्सव समिति की आधिकारिक वेबसाइट पर आपका स्वागत है।",

    "about_title": "हमारे बारे में",
    "about_text": "नव दुर्गा उत्सव समिति New Salaiya की धार्मिक, सामाजिक और सांस्कृतिक समिति है।",

    "address": "New Salaiya, Sarni, Madhya Pradesh",
    "mobile": "यहाँ मोबाइल नंबर डालें",
    "email": "यहाँ ईमेल डालें",

    "footer_text": "श्रद्धा • सेवा • संस्कार"
}

# =========================================================
# DEFAULT AARTI
# =========================================================

DEFAULT_AARTIS = [
    {
        "id": "aarti_1",
        "title": "श्री दुर्गा आरती",
        "text": "यहाँ अपनी आरती का पूरा पाठ लिखें।"
    }
]

# =========================================================
# DEFAULT PROGRAMS
# =========================================================

DEFAULT_PROGRAMS = [
    {
        "id": "program_1",
        "title": "🌸 कलश यात्रा",
        "date": "16-10-2026",
        "time": "सुबह 8:00 बजे",
        "place": "समिति प्रांगण",
        "details": "भव्य कलश यात्रा का आयोजन।"
    },
    {
        "id": "program_2",
        "title": "🙏 माता की आरती",
        "date": "16-10-2026",
        "time": "शाम 7:00 बजे",
        "place": "दुर्गा पंडाल",
        "details": "सामूहिक माता की आरती।"
    },
    {
        "id": "program_3",
        "title": "🍛 भंडारा",
        "date": "17-10-2026",
        "time": "दोपहर 12:00 बजे",
        "place": "समिति प्रांगण",
        "details": "सभी श्रद्धालुओं के लिए भंडारा।"
    },
    {
        "id": "program_4",
        "title": "🎶 सांस्कृतिक कार्यक्रम",
        "date": "18-10-2026",
        "time": "शाम 8:00 बजे",
        "place": "मुख्य मंच",
        "details": "भजन एवं सांस्कृतिक कार्यक्रम।"
    }
]

# =========================================================
# DEFAULT ACCOUNTS
# =========================================================

DEFAULT_ACCOUNTS = {
    "public_donation_amount": False,

    "donations": [
        {
            "id": "donation_1",
            "नाम": "रमेश जी",
            "तारीख": "10-09-2026",
            "राशि": 5000,
            "माध्यम": "Cash"
        },
        {
            "id": "donation_2",
            "नाम": "सुरेश जी",
            "तारीख": "11-09-2026",
            "राशि": 2500,
            "माध्यम": "UPI"
        }
    ],

    "expenses": [
        {
            "id": "expense_1",
            "खर्च": "सजावट",
            "तारीख": "11-09-2026",
            "राशि": 2500
        },
        {
            "id": "expense_2",
            "खर्च": "पूजा सामग्री",
            "तारीख": "12-09-2026",
            "राशि": 1200
        }
    ]
}

# =========================================================
# PERSISTENT STORAGE
# =========================================================
# If GitHub secrets are configured, JSON data and Gallery images
# are stored in the GitHub repository so they survive Streamlit
# Cloud restarts/redeployments.
#
# Add these to Streamlit Secrets:
# GITHUB_TOKEN = "your_github_token"
# GITHUB_REPO = "username/repository"
# GITHUB_BRANCH = "main"
# =========================================================

# GitHub persistence is optional. The app also works on a local PC
# when Streamlit secrets.toml has not been created yet.
def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        # No secrets.toml / secrets directory: use environment variables or default.
        import os
        return os.environ.get(name, default)

GITHUB_TOKEN = get_secret("GITHUB_TOKEN", "")
GITHUB_REPO = get_secret("GITHUB_REPO", "")
GITHUB_BRANCH = get_secret("GITHUB_BRANCH", "main")

GITHUB_API = "https://api.github.com"
GITHUB_ENABLED = bool(GITHUB_TOKEN and GITHUB_REPO)


def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def github_get_file(repo_path):
    if not GITHUB_ENABLED:
        return None, None

    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{repo_path}"
    response = requests.get(
        url,
        headers=github_headers(),
        params={"ref": GITHUB_BRANCH},
        timeout=20
    )

    if response.status_code == 404:
        return None, None

    response.raise_for_status()
    payload = response.json()

    if payload.get("type") != "file":
        return None, None

    raw = base64.b64decode(payload["content"])
    return raw, payload.get("sha")


def github_save_file(repo_path, raw_bytes, message):
    if not GITHUB_ENABLED:
        return False

    _, sha = github_get_file(repo_path)

    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{repo_path}"

    body = {
        "message": message,
        "content": base64.b64encode(raw_bytes).decode("utf-8"),
        "branch": GITHUB_BRANCH
    }

    if sha:
        body["sha"] = sha

    response = requests.put(
        url,
        headers=github_headers(),
        json=body,
        timeout=30
    )
    response.raise_for_status()
    return True


def github_delete_file(repo_path, message):
    if not GITHUB_ENABLED:
        return False

    _, sha = github_get_file(repo_path)

    if not sha:
        return True

    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{repo_path}"

    response = requests.delete(
        url,
        headers=github_headers(),
        json={
            "message": message,
            "sha": sha,
            "branch": GITHUB_BRANCH
        },
        timeout=30
    )
    response.raise_for_status()
    return True


def github_list_files(repo_path):
    if not GITHUB_ENABLED:
        return []

    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{repo_path}"
    response = requests.get(
        url,
        headers=github_headers(),
        params={"ref": GITHUB_BRANCH},
        timeout=20
    )

    if response.status_code == 404:
        return []

    response.raise_for_status()
    return response.json()


def save_json(file_path, data):
    raw = json.dumps(
        data,
        ensure_ascii=False,
        indent=4
    ).encode("utf-8")

    # Always keep a local copy.
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(raw)

    # Also save remotely when GitHub storage is configured.
    if GITHUB_ENABLED:
        repo_path = str(file_path.relative_to(BASE_DIR)).replace("\\", "/")
        try:
            github_save_file(
                repo_path,
                raw,
                f"Update {repo_path}"
            )
        except Exception as error:
            st.warning(f"Remote save failed; local copy kept: {error}")


def load_json(file_path, default_data):

    # Prefer the persistent GitHub copy.
    # If GitHub does not contain the file yet, upload the existing
    # local copy first so existing data is preserved.
    if GITHUB_ENABLED:
        repo_path = str(file_path.relative_to(BASE_DIR)).replace("\\", "/")
        try:
            raw, _ = github_get_file(repo_path)

            if raw:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(raw)
                return json.loads(raw.decode("utf-8"))

            if file_path.exists():
                with open(file_path, "rb") as file:
                    local_raw = file.read()
                github_save_file(
                    repo_path,
                    local_raw,
                    f"Initial backup of {repo_path}"
                )
                return json.loads(local_raw.decode("utf-8"))

        except Exception as error:
            st.warning(f"GitHub sync issue for {file_path.name}; local data kept: {error}")

    # Fall back to local storage.
    if not file_path.exists():
        save_json(file_path, default_data)
        return default_data

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception:
        save_json(file_path, default_data)
        return default_data


def sync_gallery_from_github():
    """Keep Gallery synchronized with GitHub without deleting local images."""
    if not GITHUB_ENABLED:
        return

    try:
        GALLERY_DIR.mkdir(parents=True, exist_ok=True)
        remote_files = github_list_files("assets/gallery")
        remote_names = {
            Path(item.get("name", "")).name
            for item in remote_files
            if item.get("type") == "file"
            and Path(item.get("name", "")).suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]
        }

        # First backup every existing local Gallery image that is not remote yet.
        for local_path in GALLERY_DIR.iterdir():
            if not local_path.is_file():
                continue
            if local_path.suffix.lower() not in [".png", ".jpg", ".jpeg", ".webp"]:
                continue
            if local_path.name not in remote_names:
                github_save_file(
                    f"assets/gallery/{local_path.name}",
                    local_path.read_bytes(),
                    f"Initial backup of Gallery image {local_path.name}"
                )

        # Then restore remote images missing from the local cache.
        for name in remote_names:
            local_path = GALLERY_DIR / name
            if local_path.exists():
                continue
            raw, _ = github_get_file(f"assets/gallery/{name}")
            if raw:
                local_path.write_bytes(raw)

    except Exception as error:
        # Local gallery still works if GitHub is temporarily unavailable.
        st.warning(f"Gallery backup/sync issue; local images kept: {error}")


def save_gallery_image(file_name, raw_bytes):
    local_path = GALLERY_DIR / file_name
    local_path.write_bytes(raw_bytes)

    if GITHUB_ENABLED:
        github_save_file(
            f"assets/gallery/{file_name}",
            raw_bytes,
            f"Add Gallery image {file_name}"
        )


def delete_gallery_image(file_name):
    local_path = GALLERY_DIR / file_name

    if local_path.exists():
        local_path.unlink()

    if GITHUB_ENABLED:
        github_delete_file(
            f"assets/gallery/{file_name}",
            f"Delete Gallery image {file_name}"
        )


# =========================================================
# LOAD DATA
# =========================================================

content = load_json(
    CONTENT_FILE,
    DEFAULT_CONTENT
)

aartis = load_json(
    AARTI_FILE,
    DEFAULT_AARTIS
)

programs = load_json(
    PROGRAMS_FILE,
    DEFAULT_PROGRAMS
)

accounts = load_json(
    ACCOUNT_FILE,
    DEFAULT_ACCOUNTS
)

# =========================================================
# DATA SAFETY
# =========================================================

if not isinstance(content, dict):
    content = DEFAULT_CONTENT.copy()

if not isinstance(aartis, list):
    aartis = DEFAULT_AARTIS.copy()

if not isinstance(programs, list):
    programs = DEFAULT_PROGRAMS.copy()

if not isinstance(accounts, dict):
    accounts = {
        "donations": [],
        "expenses": []
    }

if "donations" not in accounts:
    accounts["donations"] = []

if "expenses" not in accounts:
    accounts["expenses"] = []

if "public_donation_amount" not in accounts:
    accounts["public_donation_amount"] = False

# =========================================================
# SESSION STATE
# =========================================================

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if "gallery_version" not in st.session_state:
    st.session_state.gallery_version = 0

# Sync persistent Gallery from GitHub into the local cache.
sync_gallery_from_github()

# =========================================================
# CSS
# =========================================================

st.markdown("""<style>
.festival-header {position:relative; overflow:hidden; min-height:390px; margin:0 0 22px 0; padding:35px 25px 30px; border-radius:22px; border:2px solid #ffd35a; text-align:center; background:radial-gradient(circle at 72% 45%,rgba(255,137,46,.55),transparent 42%),linear-gradient(110deg,#64151d 0%,#8f2d1f 38%,#d05228 100%); box-shadow:inset 0 0 0 8px rgba(255,211,90,.08),inset 0 0 0 10px rgba(255,211,90,.35);}
.festival-header:before {content:""; position:absolute; inset:9px; border:1px solid rgba(255,220,100,.75); border-radius:17px; pointer-events:none;}
.festival-header:after {content:""; position:absolute; left:-5%; right:-5%; bottom:-170px; height:310px; border-top:2px solid rgba(255,220,100,.75); border-radius:50%; pointer-events:none;}
.header-diya {position:relative; z-index:3; margin:10px auto 28px; width:82px; height:82px; border:2px solid #ffd95a; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:43px; background:rgba(95,12,25,.20); box-shadow:0 0 18px rgba(255,214,70,.20);}
.header-title {position:relative; z-index:4; margin:0; color:#ffe18a; font-family:"Nirmala UI","Mangal",serif; font-size:clamp(34px,5vw,67px); font-weight:900; line-height:1.25; text-shadow:3px 3px 0 #551019,5px 5px 8px rgba(0,0,0,.45);}
.header-line {position:relative; z-index:4; width:220px; height:2px; margin:20px auto 10px; background:#ffd85d;}
.header-dot {position:relative; z-index:4; color:#ffe28b; font-size:25px; line-height:1;}
.header-location {position:relative; z-index:4; margin-top:18px; color:#ffe58a; font-family:Arial,sans-serif; font-size:23px; font-weight:800; letter-spacing:1px;}
.header-tagline {position:relative; z-index:4; display:inline-block; margin-top:28px; padding:11px 55px; min-width:420px; border:1px solid #ffd85d; border-radius:45px; color:#ffe7a0; background:rgba(82,5,24,.82); font-family:"Nirmala UI","Mangal",serif; font-size:27px; font-weight:600; box-shadow:0 3px 12px rgba(0,0,0,.25);}
.header-arc {position:absolute; z-index:1; width:410px; height:260px; border:2px solid rgba(255,220,100,.75); border-bottom:0; border-radius:50% 50% 0 0; pointer-events:none;}
.arc-left {left:-120px; bottom:-60px; transform:rotate(-3deg);}
.arc-right {right:-120px; bottom:-60px; transform:rotate(3deg);}
.hero-box {padding:35px; border-radius:25px; text-align:center; border:1px solid rgba(128,128,128,.30); margin-bottom:25px;}
.footer-text {text-align:center; opacity:.70; padding:15px;}
@media (max-width:700px){.festival-header{min-height:330px;padding:25px 10px}.header-tagline{min-width:0;width:88%;padding:11px 8px;font-size:21px}.header-title{font-size:36px}.header-arc{width:300px;height:210px}.header-diya{margin-bottom:18px}}
</style>""", unsafe_allow_html=True)

# =========================================================
# WEBSITE HEADER
# =========================================================

header_name = content.get("committee_name", "नव दुर्गा उत्सव समिति")
header_location = content.get("location", "NEW SALAIYA").upper()

st.markdown(f"""<div class="festival-header">
<div class="header-arc arc-left"></div>
<div class="header-arc arc-right"></div>
<div class="header-diya">🪔</div>
<div class="header-title">{header_name}</div>
<div class="header-line"></div>
<div class="header-dot">•</div>
<div class="header-location">{header_location}</div>
<div class="header-tagline">✧ &nbsp; श्रद्धा • सेवा • संस्कार &nbsp; ✧</div>
</div>""", unsafe_allow_html=True)

# =========================================================
# MENU
# =========================================================

menu = st.radio(
    "Menu",
    [
        "🏠 Home",
        "ℹ️ About",
        "🎉 कार्यक्रम",
        "🖼️ Gallery",
        "💰 हिसाब-किताब",
        "🙏 आरती",
        "📞 संपर्क करें",
        "🔐 Admin Panel"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# =========================================================
# HOME
# =========================================================

if menu == "🏠 Home":

    st.markdown(
        '<div class="hero-box">',
        unsafe_allow_html=True
    )

    st.title(
        content.get(
            "home_title",
            "जय माता दी 🙏"
        )
    )

    st.write(
        content.get(
            "home_text",
            ""
        )
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # Main image
    image_files = [
        p for p in ASSETS_DIR.iterdir()
        if p.is_file()
        and p.suffix.lower()
        in [".png", ".jpg", ".jpeg", ".webp"]
    ]

    if image_files:

        st.image(
            str(image_files[0]),
            use_container_width=True
        )

    st.subheader("🌺 समिति की विशेषताएँ")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("🙏 भक्ति")

    with col2:
        st.success("🤝 एकता")

    with col3:
        st.warning("❤️ सेवा")


# =========================================================
# ABOUT
# =========================================================

elif menu == "ℹ️ About":

    st.title(
        content.get(
            "about_title",
            "हमारे बारे में"
        )
    )

    st.write(
        content.get(
            "about_text",
            ""
        )
    )

    st.subheader("📍 हमारा पता")

    st.write(
        content.get(
            "address",
            ""
        )
    )


# =========================================================
# PROGRAMS
# =========================================================

elif menu == "🎉 कार्यक्रम":

    st.title("🎉 कार्यक्रम")

    if programs:

        for program in programs:

            with st.container(border=True):

                st.subheader(
                    program.get(
                        "title",
                        "कार्यक्रम"
                    )
                )

                st.write(
                    "📅 तारीख:",
                    program.get(
                        "date",
                        ""
                    )
                )

                st.write(
                    "⏰ समय:",
                    program.get(
                        "time",
                        ""
                    )
                )

                st.write(
                    "📍 स्थान:",
                    program.get(
                        "place",
                        ""
                    )
                )

                if program.get("details"):

                    st.write(
                        program.get(
                            "details",
                            ""
                        )
                    )

    else:

        st.info(
            "अभी कोई कार्यक्रम उपलब्ध नहीं है।"
        )


# =========================================================
# GALLERY
# =========================================================

elif menu == "🖼️ Gallery":

    st.title("🖼️ समिति Gallery")

    st.write(
        "समिति की यादगार तस्वीरें यहाँ देखें।"
    )

    uploaded_image = st.file_uploader(
        "📷 Gallery में image upload करें",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp"
        ],
        key=f"gallery_{st.session_state.gallery_version}"
    )

    if uploaded_image is not None:

        file_name = (
            f"{uuid.uuid4().hex}_"
            f"{Path(uploaded_image.name).name}"
        )

        save_path = GALLERY_DIR / file_name

        try:
            save_gallery_image(
                file_name,
                uploaded_image.getvalue()
            )
        except Exception as error:
            st.error(f"Image save नहीं हुई: {error}")
            st.stop()

        st.success(
            "Image Gallery में upload हो गई।"
        )

        st.session_state.gallery_version += 1

        st.rerun()

    gallery_images = sorted(
        [
            file
            for file in GALLERY_DIR.iterdir()
            if file.is_file()
            and file.suffix.lower()
            in [
                ".png",
                ".jpg",
                ".jpeg",
                ".webp"
            ]
        ]
    )

    st.write(
        f"📸 कुल तस्वीरें: {len(gallery_images)}"
    )

    if gallery_images:

        columns = st.columns(3)

        for index, image_path in enumerate(
            gallery_images
        ):

            with columns[index % 3]:

                st.image(
                    str(image_path),
                    use_container_width=True
                )

    else:

        st.info(
            "अभी Gallery में कोई image नहीं है।"
        )


# =========================================================
# ACCOUNTS
# =========================================================

elif menu == "💰 हिसाब-किताब":

    st.title("💰 हिसाब-किताब")

    total_donation = sum(
        float(item.get("राशि", 0) or 0)
        for item in accounts["donations"]
    )

    total_expense = sum(
        float(item.get("राशि", 0) or 0)
        for item in accounts["expenses"]
    )

    balance = total_donation - total_expense

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "📥 कुल चंदा",
            f"₹{total_donation:,.0f}"
        )

    with col2:
        st.metric(
            "📤 कुल खर्च",
            f"₹{total_expense:,.0f}"
        )

    with col3:
        st.metric(
            "💵 शेष राशि",
            f"₹{balance:,.0f}"
        )

    st.divider()

    # =========================================================
    # DONATION SECTION
    # =========================================================

    donation_title_col, donation_button_col = st.columns([6, 1])

    with donation_title_col:
        st.subheader("📥 चंदा")

    with donation_button_col:
        add_donation_public = st.button(
            "➕",
            key="public_add_donation_button",
            use_container_width=True
        )

    if add_donation_public:
        st.session_state["show_public_donation_form"] = True

    if "show_public_donation_form" not in st.session_state:
        st.session_state["show_public_donation_form"] = False

    if st.session_state["show_public_donation_form"]:

        with st.container(border=True):

            st.write("➕ **नया चंदा जोड़ें**")
            st.info("चंदा जोड़ने के लिए Admin Password डालें।")

            public_donation_password = st.text_input(
                "Admin Password",
                type="password",
                key="public_donation_password"
            )

            if public_donation_password == ADMIN_PASSWORD:

                with st.form("public_donation_form"):

                    donor_name_public = st.text_input("नाम")

                    donor_date_public = st.text_input(
                        "तारीख",
                        placeholder="जैसे 16-09-2026"
                    )

                    donor_amount_public = st.number_input(
                        "राशि",
                        min_value=0,
                        step=100
                    )

                    donor_method_public = st.selectbox(
                        "माध्यम",
                        [
                            "Cash",
                            "UPI",
                            "Bank",
                            "Other"
                        ]
                    )

                    save_public_donation = st.form_submit_button(
                        "💾 चंदा सेव करें"
                    )

                    if save_public_donation:

                        if not donor_name_public.strip():
                            st.warning("नाम भरें।")

                        elif donor_amount_public <= 0:
                            st.warning("राशि 0 से ज्यादा रखें।")

                        else:
                            accounts["donations"].append(
                                {
                                    "id": f"donation_{uuid.uuid4().hex}",
                                    "नाम": donor_name_public.strip(),
                                    "तारीख": donor_date_public.strip(),
                                    "राशि": donor_amount_public,
                                    "माध्यम": donor_method_public
                                }
                            )

                            save_json(
                                ACCOUNT_FILE,
                                accounts
                            )

                            st.success(
                                "चंदा सफलतापूर्वक जोड़ दिया गया।"
                            )

                            st.session_state[
                                "show_public_donation_form"
                            ] = False

                            st.rerun()

            elif public_donation_password:
                st.error("Password गलत है।")

            if st.button(
                "✖ बंद करें",
                key="close_public_donation_form"
            ):
                st.session_state[
                    "show_public_donation_form"
                ] = False
                st.rerun()

    if accounts["donations"]:

        donation_rows = []

        for number, item in enumerate(
            accounts["donations"],
            start=1
        ):

            amount_is_public = accounts.get("public_donation_amount", False)

        donation_rows.append(
                {
                    "क्र.": number,
                    "👤 नाम": item.get("नाम", ""),
                    "📅 तारीख": item.get("तारीख", ""),
                    "💰 राशि": f"₹{float(item.get('राशि', 0)):,.0f}" if amount_is_public else "...",
                    "💳 माध्यम": item.get("माध्यम", "")
                }
            )

        st.table(donation_rows)

    else:
        st.info("अभी कोई चंदा दर्ज नहीं है।")

    st.divider()

    # =========================================================
    # EXPENSE SECTION
    # =========================================================

    expense_title_col, expense_button_col = st.columns([6, 1])

    with expense_title_col:
        st.subheader("📤 खर्च")

    with expense_button_col:
        add_expense_public = st.button(
            "➕",
            key="public_add_expense_button",
            use_container_width=True
        )

    if add_expense_public:
        st.session_state["show_public_expense_form"] = True

    if "show_public_expense_form" not in st.session_state:
        st.session_state["show_public_expense_form"] = False

    if st.session_state["show_public_expense_form"]:

        with st.container(border=True):

            st.write("➕ **नया खर्च जोड़ें**")
            st.info("खर्च जोड़ने के लिए Admin Password डालें।")

            public_expense_password = st.text_input(
                "Admin Password",
                type="password",
                key="public_expense_password"
            )

            if public_expense_password == ADMIN_PASSWORD:

                with st.form("public_expense_form"):

                    expense_name_public = st.text_input(
                        "खर्च का नाम"
                    )

                    expense_date_public = st.text_input(
                        "तारीख",
                        placeholder="जैसे 16-09-2026"
                    )

                    expense_amount_public = st.number_input(
                        "राशि",
                        min_value=0,
                        step=100
                    )

                    save_public_expense = st.form_submit_button(
                        "💾 खर्च सेव करें"
                    )

                    if save_public_expense:

                        if not expense_name_public.strip():
                            st.warning("खर्च का नाम भरें।")

                        elif expense_amount_public <= 0:
                            st.warning(
                                "राशि 0 से ज्यादा रखें।"
                            )

                        else:
                            accounts["expenses"].append(
                                {
                                    "id": f"expense_{uuid.uuid4().hex}",
                                    "खर्च": expense_name_public.strip(),
                                    "तारीख": expense_date_public.strip(),
                                    "राशि": expense_amount_public
                                }
                            )

                            save_json(
                                ACCOUNT_FILE,
                                accounts
                            )

                            st.success(
                                "खर्च सफलतापूर्वक जोड़ दिया गया।"
                            )

                            st.session_state[
                                "show_public_expense_form"
                            ] = False

                            st.rerun()

            elif public_expense_password:
                st.error("Password गलत है।")

            if st.button(
                "✖ बंद करें",
                key="close_public_expense_form"
            ):
                st.session_state[
                    "show_public_expense_form"
                ] = False
                st.rerun()

    if accounts["expenses"]:

        expense_rows = []

        for number, item in enumerate(
            accounts["expenses"],
            start=1
        ):

            expense_rows.append(
                {
                    "क्र.": number,
                    "🧾 खर्च": item.get("खर्च", ""),
                    "📅 तारीख": item.get("तारीख", ""),
                    "💰 राशि": f"₹{float(item.get('राशि', 0)):,.0f}"
                }
            )

        st.table(expense_rows)

    else:
        st.info("अभी कोई खर्च दर्ज नहीं है।")

    st.divider()

    # =========================================================
    # FINAL SUMMARY
    # =========================================================

    st.subheader("📊 हिसाब का सारांश")

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.write("📥 **कुल चंदा**")
        st.write(f"### ₹{total_donation:,.0f}")

    with summary_col2:
        st.write("📤 **कुल खर्च**")
        st.write(f"### ₹{total_expense:,.0f}")

    with summary_col3:
        st.write("💵 **बाकी राशि**")
        st.write(f"### ₹{balance:,.0f}")


# =========================================================
# AARTI
# =========================================================

elif menu == "🙏 आरती":

    st.title("🙏 आरती")

    if aartis:

        for index, aarti in enumerate(aartis):

            with st.expander(
                f"🙏 {aarti.get('title', 'आरती')}",
                expanded=(index == 0)
            ):

                st.write(
                    aarti.get(
                        "text",
                        ""
                    )
                )

    else:

        st.info(
            "अभी कोई आरती नहीं है।"
        )

    st.divider()

    # PLUS BUTTON
    with st.expander("➕ नई आरती जोड़ें"):

        st.info(
            "नई आरती जोड़ने के लिए Admin Password डालें।"
        )

        aarti_password = st.text_input(
            "Admin Password",
            type="password",
            key="public_aarti_password"
        )

        if aarti_password:

            if aarti_password == ADMIN_PASSWORD:

                with st.form(
                    "new_aarti_form"
                ):

                    new_title = st.text_input(
                        "आरती का नाम"
                    )

                    new_text = st.text_area(
                        "आरती का पूरा पाठ",
                        height=250
                    )

                    add_button = st.form_submit_button(
                        "➕ आरती जोड़ें"
                    )

                    if add_button:

                        if (
                            not new_title.strip()
                            or
                            not new_text.strip()
                        ):

                            st.warning(
                                "आरती का नाम और पाठ दोनों भरें।"
                            )

                        else:

                            aartis.append(
                                {
                                    "id":
                                    f"aarti_{uuid.uuid4().hex}",

                                    "title":
                                    new_title.strip(),

                                    "text":
                                    new_text.strip()
                                }
                            )

                            save_json(
                                AARTI_FILE,
                                aartis
                            )

                            st.success(
                                "नई आरती जोड़ दी गई।"
                            )

                            st.rerun()

            else:

                st.error(
                    "Password गलत है।"
                )


# =========================================================
# CONTACT
# =========================================================

elif menu == "📞 संपर्क करें":

    st.title("📞 संपर्क करें")

    st.write(
        f"📍 पता: "
        f"{content.get('address', '')}"
    )

    st.write(
        f"📱 मोबाइल: "
        f"{content.get('mobile', '')}"
    )

    st.write(
        f"📧 Email: "
        f"{content.get('email', '')}"
    )


# =========================================================
# ADMIN PANEL
# =========================================================

elif menu == "🔐 Admin Panel":

    st.title("🔐 Admin Panel")

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    if not st.session_state.admin_logged_in:

        password = st.text_input(
            "Admin Password",
            type="password",
            key="admin_password"
        )

        if st.button("🔓 Login"):

            if password == ADMIN_PASSWORD:

                st.session_state.admin_logged_in = True

                st.rerun()

            else:

                st.error(
                    "Password गलत है।"
                )

    # -----------------------------------------------------
    # ADMIN LOGGED IN
    # -----------------------------------------------------

    else:

        st.success(
            "Admin login successful."
        )

        if GITHUB_ENABLED:
            st.success("☁️ Permanent storage: GitHub connected")
        else:
            st.info(
                "💾 Local storage active. Permanent cloud storage के लिए "
                "GITHUB_TOKEN और GITHUB_REPO Secrets सेट करें।"
            )

        if st.button("🚪 Logout"):

            st.session_state.admin_logged_in = False

            st.rerun()

        admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = st.tabs(
            [
                "✏️ Website Edit",
                "🙏 आरती Edit",
                "🎉 कार्यक्रम Edit",
                "🖼️ Gallery Edit",
                "💰 हिसाब Edit"
            ]
        )

        # =================================================
        # PUBLIC DONATION AMOUNT VISIBILITY
        # =================================================

        st.divider()
        st.subheader("👁️ चंदा राशि Public / Private")

        current_amount_visibility = accounts.get(
            "public_donation_amount",
            False
        )

        amount_visibility = st.toggle(
            "💰 Public Website पर चंदे की राशि दिखाएँ",
            value=current_amount_visibility,
            key="public_donation_amount_toggle"
        )

        if amount_visibility != current_amount_visibility:
            accounts["public_donation_amount"] = amount_visibility
            save_json(ACCOUNT_FILE, accounts)
            st.rerun()

        if amount_visibility:
            st.success("🟢 ON: Public को चंदे की पूरी राशि दिखाई देगी।")
        else:
            st.info("🔒 OFF: Public को राशि की जगह केवल ... दिखाई देगा।")

        # =================================================
        # WEBSITE EDIT
        # =================================================

        with admin_tab1:

            st.subheader(
                "✏️ Website Content Edit"
            )

            with st.form(
                "website_edit_form"
            ):

                committee_name = st.text_input(
                    "Committee Name",
                    value=content.get(
                        "committee_name",
                        ""
                    )
                )

                location = st.text_input(
                    "Location",
                    value=content.get(
                        "location",
                        ""
                    )
                )

                tagline = st.text_input(
                    "Tagline",
                    value=content.get(
                        "tagline",
                        ""
                    )
                )

                home_title = st.text_input(
                    "Home Title",
                    value=content.get(
                        "home_title",
                        ""
                    )
                )

                home_text = st.text_area(
                    "Home Text",
                    value=content.get(
                        "home_text",
                        ""
                    ),
                    height=120
                )

                about_title = st.text_input(
                    "About Title",
                    value=content.get(
                        "about_title",
                        ""
                    )
                )

                about_text = st.text_area(
                    "About Text",
                    value=content.get(
                        "about_text",
                        ""
                    ),
                    height=160
                )

                address = st.text_input(
                    "Address",
                    value=content.get(
                        "address",
                        ""
                    )
                )

                mobile = st.text_input(
                    "Mobile",
                    value=content.get(
                        "mobile",
                        ""
                    )
                )

                email = st.text_input(
                    "Email",
                    value=content.get(
                        "email",
                        ""
                    )
                )

                footer_text = st.text_input(
                    "Footer Text",
                    value=content.get(
                        "footer_text",
                        ""
                    )
                )

                save_button = st.form_submit_button(
                    "💾 Save Website"
                )

                if save_button:

                    content = {
                        "committee_name":
                        committee_name,

                        "location":
                        location,

                        "tagline":
                        tagline,

                        "home_title":
                        home_title,

                        "home_text":
                        home_text,

                        "about_title":
                        about_title,

                        "about_text":
                        about_text,

                        "address":
                        address,

                        "mobile":
                        mobile,

                        "email":
                        email,

                        "footer_text":
                        footer_text
                    }

                    save_json(
                        CONTENT_FILE,
                        content
                    )

                    st.success(
                        "Website content save हो गया।"
                    )

                    st.rerun()

        # =================================================
        # AARTI EDIT
        # =================================================

        with admin_tab2:

            st.subheader(
                "🙏 आरती Manage करें"
            )

            # ADD AARTI
            with st.form(
                "admin_add_aarti_form"
            ):

                st.write(
                    "➕ नई आरती"
                )

                new_aarti_title = st.text_input(
                    "आरती का नाम"
                )

                new_aarti_text = st.text_area(
                    "आरती का पूरा पाठ",
                    height=250
                )

                add_aarti = st.form_submit_button(
                    "➕ Add Aarti"
                )

                if add_aarti:

                    if (
                        not new_aarti_title.strip()
                        or
                        not new_aarti_text.strip()
                    ):

                        st.warning(
                            "आरती का नाम और पाठ दोनों भरें।"
                        )

                    else:

                        aartis.append(
                            {
                                "id":
                                f"aarti_{uuid.uuid4().hex}",

                                "title":
                                new_aarti_title.strip(),

                                "text":
                                new_aarti_text.strip()
                            }
                        )

                        save_json(
                            AARTI_FILE,
                            aartis
                        )

                        st.success(
                            "नई आरती add हो गई।"
                        )

                        st.rerun()

            st.divider()

            st.subheader(
                "✏️ Existing आरती"
            )

            for index, aarti in enumerate(aartis):

                with st.expander(
                    f"🙏 {aarti.get('title', 'आरती')}"
                ):

                    edit_title = st.text_input(
                        "आरती का नाम",
                        value=aarti.get(
                            "title",
                            ""
                        ),
                        key=f"aarti_title_{index}"
                    )

                    edit_text = st.text_area(
                        "आरती का पाठ",
                        value=aarti.get(
                            "text",
                            ""
                        ),
                        height=250,
                        key=f"aarti_text_{index}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "💾 Save",
                            key=f"save_aarti_{index}"
                        ):

                            aartis[index]["title"] = (
                                edit_title
                            )

                            aartis[index]["text"] = (
                                edit_text
                            )

                            save_json(
                                AARTI_FILE,
                                aartis
                            )

                            st.success(
                                "आरती update हो गई।"
                            )

                            st.rerun()

                    with col2:

                        if st.button(
                            "🗑️ Delete",
                            key=f"delete_aarti_{index}"
                        ):

                            aartis.pop(index)

                            save_json(
                                AARTI_FILE,
                                aartis
                            )

                            st.success(
                                "आरती delete हो गई।"
                            )

                            st.rerun()

        # =================================================
        # PROGRAM EDIT
        # =================================================

        with admin_tab3:

            st.subheader(
                "🎉 कार्यक्रम Manage करें"
            )

            # ADD PROGRAM
            with st.form(
                "add_program_form"
            ):

                st.write(
                    "➕ नया कार्यक्रम"
                )

                program_title = st.text_input(
                    "कार्यक्रम का नाम"
                )

                program_date = st.text_input(
                    "तारीख",
                    placeholder="जैसे 20-10-2026"
                )

                program_time = st.text_input(
                    "समय",
                    placeholder="जैसे शाम 7:00 बजे"
                )

                program_place = st.text_input(
                    "स्थान"
                )

                program_details = st.text_area(
                    "विवरण",
                    height=100
                )

                add_program = st.form_submit_button(
                    "➕ कार्यक्रम जोड़ें"
                )

                if add_program:

                    if not program_title.strip():

                        st.warning(
                            "कार्यक्रम का नाम भरें।"
                        )

                    else:

                        programs.append(
                            {
                                "id":
                                f"program_{uuid.uuid4().hex}",

                                "title":
                                program_title.strip(),

                                "date":
                                program_date.strip(),

                                "time":
                                program_time.strip(),

                                "place":
                                program_place.strip(),

                                "details":
                                program_details.strip()
                            }
                        )

                        save_json(
                            PROGRAMS_FILE,
                            programs
                        )

                        st.success(
                            "नया कार्यक्रम add हो गया।"
                        )

                        st.rerun()

            st.divider()

            st.subheader(
                "✏️ Existing कार्यक्रम"
            )

            for index, program in enumerate(programs):

                with st.expander(
                    f"🎉 {program.get('title', 'कार्यक्रम')}"
                ):

                    edit_program_title = st.text_input(
                        "कार्यक्रम का नाम",
                        value=program.get(
                            "title",
                            ""
                        ),
                        key=f"program_title_{index}"
                    )

                    edit_program_date = st.text_input(
                        "तारीख",
                        value=program.get(
                            "date",
                            ""
                        ),
                        key=f"program_date_{index}"
                    )

                    edit_program_time = st.text_input(
                        "समय",
                        value=program.get(
                            "time",
                            ""
                        ),
                        key=f"program_time_{index}"
                    )

                    edit_program_place = st.text_input(
                        "स्थान",
                        value=program.get(
                            "place",
                            ""
                        ),
                        key=f"program_place_{index}"
                    )

                    edit_program_details = st.text_area(
                        "विवरण",
                        value=program.get(
                            "details",
                            ""
                        ),
                        height=100,
                        key=f"program_details_{index}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "💾 Save",
                            key=f"save_program_{index}"
                        ):

                            programs[index]["title"] = (
                                edit_program_title
                            )

                            programs[index]["date"] = (
                                edit_program_date
                            )

                            programs[index]["time"] = (
                                edit_program_time
                            )

                            programs[index]["place"] = (
                                edit_program_place
                            )

                            programs[index]["details"] = (
                                edit_program_details
                            )

                            save_json(
                                PROGRAMS_FILE,
                                programs
                            )

                            st.success(
                                "कार्यक्रम update हो गया।"
                            )

                            st.rerun()

                    with col2:

                        if st.button(
                            "🗑️ Delete",
                            key=f"delete_program_{index}"
                        ):

                            programs.pop(index)

                            save_json(
                                PROGRAMS_FILE,
                                programs
                            )

                            st.success(
                                "कार्यक्रम delete हो गया।"
                            )

                            st.rerun()

        # =================================================
        # GALLERY EDIT
        # =================================================

        with admin_tab4:

            st.subheader(
                "🖼️ Gallery Manage करें"
            )

            gallery_images = sorted(
                [
                    file
                    for file in GALLERY_DIR.iterdir()
                    if file.is_file()
                    and file.suffix.lower()
                    in [
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".webp"
                    ]
                ]
            )

            st.write(
                f"📸 कुल images: {len(gallery_images)}"
            )

            if gallery_images:

                if st.button(
                    "🗑️ Delete ALL Gallery Images"
                ):

                    for image_path in gallery_images:
                        try:
                            delete_gallery_image(image_path.name)
                        except Exception:
                            pass

                    st.success(
                        "सभी Gallery images delete हो गईं।"
                    )

                    st.rerun()

                for index, image_path in enumerate(
                    gallery_images
                ):

                    with st.expander(
                        f"🖼️ {image_path.name}"
                    ):

                        st.image(
                            str(image_path),
                            use_container_width=True
                        )

                        if st.button(
                            "🗑️ Delete this image",
                            key=f"delete_gallery_{index}"
                        ):

                            try:
                                delete_gallery_image(image_path.name)

                                st.success(
                                    "Image delete हो गई।"
                                )

                                st.rerun()

                            except Exception as error:

                                st.error(
                                    f"Image delete नहीं हुई: {error}"
                                )

            else:

                st.info(
                    "Gallery खाली है।"
                )

        # =================================================
        # ACCOUNT EDIT
        # =================================================

        with admin_tab5:

            st.subheader(
                "💰 हिसाब-किताब Manage करें"
            )

            account_tab1, account_tab2 = st.tabs(
                [
                    "📥 चंदा जोड़ें",
                    "📤 खर्च जोड़ें"
                ]
            )

            # ------------------------------------------------
            # ADD DONATION
            # ------------------------------------------------

            with account_tab1:

                with st.form(
                    "donation_form"
                ):

                    donor_name = st.text_input(
                        "नाम"
                    )

                    donor_date = st.text_input(
                        "तारीख",
                        placeholder="जैसे 16-09-2026"
                    )

                    donor_amount = st.number_input(
                        "राशि",
                        min_value=0,
                        step=100
                    )

                    donor_method = st.selectbox(
                        "माध्यम",
                        [
                            "Cash",
                            "UPI",
                            "Bank",
                            "Other"
                        ]
                    )

                    add_donation = st.form_submit_button(
                        "➕ चंदा जोड़ें"
                    )

                    if add_donation:

                        if not donor_name.strip():

                            st.warning(
                                "नाम भरें।"
                            )

                        elif donor_amount <= 0:

                            st.warning(
                                "राशि 0 से ज्यादा रखें।"
                            )

                        else:

                            accounts["donations"].append(
                                {
                                    "id":
                                    f"donation_{uuid.uuid4().hex}",

                                    "नाम":
                                    donor_name.strip(),

                                    "तारीख":
                                    donor_date.strip(),

                                    "राशि":
                                    donor_amount,

                                    "माध्यम":
                                    donor_method
                                }
                            )

                            save_json(
                                ACCOUNT_FILE,
                                accounts
                            )

                            st.success(
                                "चंदा add हो गया।"
                            )

                            st.rerun()

            # ------------------------------------------------
            # ADD EXPENSE
            # ------------------------------------------------

            with account_tab2:

                with st.form(
                    "expense_form"
                ):

                    expense_name = st.text_input(
                        "खर्च का नाम"
                    )

                    expense_date = st.text_input(
                        "तारीख",
                        placeholder="जैसे 16-09-2026"
                    )

                    expense_amount = st.number_input(
                        "राशि",
                        min_value=0,
                        step=100
                    )

                    add_expense = st.form_submit_button(
                        "➕ खर्च जोड़ें"
                    )

                    if add_expense:

                        if not expense_name.strip():

                            st.warning(
                                "खर्च का नाम भरें।"
                            )

                        elif expense_amount <= 0:

                            st.warning(
                                "राशि 0 से ज्यादा रखें।"
                            )

                        else:

                            accounts["expenses"].append(
                                {
                                    "id":
                                    f"expense_{uuid.uuid4().hex}",

                                    "खर्च":
                                    expense_name.strip(),

                                    "तारीख":
                                    expense_date.strip(),

                                    "राशि":
                                    expense_amount
                                }
                            )

                            save_json(
                                ACCOUNT_FILE,
                                accounts
                            )

                            st.success(
                                "खर्च add हो गया।"
                            )

                            st.rerun()

            st.divider()

            # =================================================
            # DONATION EDIT
            # =================================================

            st.subheader(
                "📥 चंदा Edit / Delete"
            )

            for index, item in enumerate(
                accounts["donations"]
            ):

                with st.expander(
                    f"👤 {item.get('नाम', 'नाम')} "
                    f"— ₹{float(item.get('राशि', 0)):,.0f}"
                ):

                    d_name = st.text_input(
                        "नाम",
                        value=item.get(
                            "नाम",
                            ""
                        ),
                        key=f"d_name_{index}"
                    )

                    d_date = st.text_input(
                        "तारीख",
                        value=item.get(
                            "तारीख",
                            ""
                        ),
                        key=f"d_date_{index}"
                    )

                    d_amount = st.number_input(
                        "राशि",
                        min_value=0,
                        value=int(
                            float(
                                item.get(
                                    "राशि",
                                    0
                                )
                            )
                        ),
                        step=100,
                        key=f"d_amount_{index}"
                    )

                    methods = [
                        "Cash",
                        "UPI",
                        "Bank",
                        "Other"
                    ]

                    old_method = item.get(
                        "माध्यम",
                        "Cash"
                    )

                    if old_method not in methods:
                        old_method = "Cash"

                    d_method = st.selectbox(
                        "माध्यम",
                        methods,
                        index=methods.index(
                            old_method
                        ),
                        key=f"d_method_{index}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "💾 Save",
                            key=f"save_donation_{index}"
                        ):

                            accounts["donations"][index] = {
                                "id":
                                item.get(
                                    "id",
                                    f"donation_{uuid.uuid4().hex}"
                                ),

                                "नाम":
                                d_name,

                                "तारीख":
                                d_date,

                                "राशि":
                                d_amount,

                                "माध्यम":
                                d_method
                            }

                            save_json(
                                ACCOUNT_FILE,
                                accounts
                            )

                            st.success(
                                "चंदा update हो गया।"
                            )

                            st.rerun()

                    with col2:

                        if st.button(
                            "🗑️ Delete",
                            key=f"delete_donation_{index}"
                        ):

                            accounts["donations"].pop(
                                index
                            )

                            save_json(
                                ACCOUNT_FILE,
                                accounts
                            )

                            st.success(
                                "चंदा delete हो गया।"
                            )

                            st.rerun()

            # =================================================
            # EXPENSE EDIT
            # =================================================

            st.subheader(
                "📤 खर्च Edit / Delete"
            )

            for index, item in enumerate(
                accounts["expenses"]
            ):

                with st.expander(
                    f"🧾 {item.get('खर्च', 'खर्च')} "
                    f"— ₹{float(item.get('राशि', 0)):,.0f}"
                ):

                    e_name = st.text_input(
                        "खर्च",
                        value=item.get(
                            "खर्च",
                            ""
                        ),
                        key=f"e_name_{index}"
                    )

                    e_date = st.text_input(
                        "तारीख",
                        value=item.get(
                            "तारीख",
                            ""
                        ),
                        key=f"e_date_{index}"
                    )

                    e_amount = st.number_input(
                        "राशि",
                        min_value=0,
                        value=int(
                            float(
                                item.get(
                                    "राशि",
                                    0
                                )
                            )
                        ),
                        step=100,
                        key=f"e_amount_{index}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "💾 Save",
                            key=f"save_expense_{index}"
                        ):

                            accounts["expenses"][index] = {
                                "id":
                                item.get(
                                    "id",
                                    f"expense_{uuid.uuid4().hex}"
                                ),

                                "खर्च":
                                e_name,

                                "तारीख":
                                e_date,

                                "राशि":
                                e_amount
                            }

                            save_json(
                                ACCOUNT_FILE,
                                accounts
                            )

                            st.success(
                                "खर्च update हो गया।"
                            )

                            st.rerun()

                    with col2:

                        if st.button(
                            "🗑️ Delete",
                            key=f"delete_expense_{index}"
                        ):

                            accounts["expenses"].pop(
                                index
                            )

                            save_json(
                                ACCOUNT_FILE,
                                accounts
                            )

                            st.success(
                                "खर्च delete हो गया।"
                            )

                            st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown(
    f"""
    <div class="footer-text">
        🙏 {content.get("footer_text", "श्रद्धा • सेवा • संस्कार")}
    </div>
    """,
    unsafe_allow_html=True
)
