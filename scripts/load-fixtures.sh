#!/bin/bash
# ==============================================================================
# ProctorWise - Load Fixture Data
# ==============================================================================
# Usage: bash scripts/load-fixtures.sh
# Run from the VPS after all containers are up and healthy.
# ==============================================================================

set -e

USER_URL="http://localhost:8001"
EXAM_URL="http://localhost:8000"

echo "=============================="
echo "ProctorWise - Loading Fixtures"
echo "=============================="

# --------------------------------------------------------------------------
# 1. Create test users
# --------------------------------------------------------------------------
echo ""
echo "[1/4] Creating test users..."

R1=$(curl -s -X POST "$USER_URL/users/register" -H "Content-Type: application/json" -d '{"name":"Alice Student","email":"alice@student.com","password":"password123","role":"student"}')
echo "  alice@student.com (student): $R1"

R2=$(curl -s -X POST "$USER_URL/users/register" -H "Content-Type: application/json" -d '{"name":"Bob Teacher","email":"bob@teacher.com","password":"password123","role":"teacher"}')
echo "  bob@teacher.com (teacher): $R2"

R3=$(curl -s -X POST "$USER_URL/users/register" -H "Content-Type: application/json" -d '{"name":"Charlie Proctor","email":"charlie@proctor.com","password":"password123","role":"proctor"}')
echo "  charlie@proctor.com (proctor): $R3"

R4=$(curl -s -X POST "$USER_URL/users/register" -H "Content-Type: application/json" -d '{"name":"Diana Admin","email":"diana@admin.com","password":"password123","role":"admin"}')
echo "  diana@admin.com (admin): $R4"

# --------------------------------------------------------------------------
# 2. Login as teacher to get JWT token + user_id
# --------------------------------------------------------------------------
echo ""
echo "[2/4] Logging in as teacher..."

LOGIN_RESP=$(curl -s -X POST "$USER_URL/users/login" -H "Content-Type: application/json" -d '{"email":"bob@teacher.com","password":"password123"}')
TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['access_token'])" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
    echo "ERROR: Could not get teacher token."
    echo "Response: $LOGIN_RESP"
    exit 1
fi
echo "Teacher token obtained."

# Extract teacher user_id from login response
TEACHER_ID=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['user']['user_id'])" 2>/dev/null || echo "")
echo "Teacher ID: $TEACHER_ID"

AUTH="Authorization: Bearer $TOKEN"

# --------------------------------------------------------------------------
# 3. Create exams with time slots and questions
# --------------------------------------------------------------------------
echo ""
echo "[3/4] Creating exams, slots, and questions..."

TOMORROW=$(date -d "+1 day" "+%Y-%m-%d" 2>/dev/null || date -v+1d "+%Y-%m-%d" 2>/dev/null || echo "2026-01-30")
echo "Slots scheduled for: $TOMORROW"

# --- Exam 1: Mathematiques ---
echo ""
echo "--- Exam 1: Mathematiques ---"
EXAM1=$(curl -s -X POST "$EXAM_URL/exams/" -H "Content-Type: application/json" -H "$AUTH" -d "{\"title\":\"Mathematiques Fondamentales\",\"description\":\"Examen de maths niveau L1\",\"duration_minutes\":60,\"teacher_id\":\"$TEACHER_ID\"}")
EXAM1_ID=$(echo "$EXAM1" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['exam_id'])" 2>/dev/null || echo "")

if [ -n "$EXAM1_ID" ]; then
    echo "  Created (ID: $EXAM1_ID)"
    curl -s -X POST "$EXAM_URL/exams/$EXAM1_ID/slots" -H "Content-Type: application/json" -H "$AUTH" -d "{\"start_time\":\"${TOMORROW}T08:00:00\"}" > /dev/null && echo "  Slot: ${TOMORROW} 08:00"
    curl -s -X POST "$EXAM_URL/exams/$EXAM1_ID/slots" -H "Content-Type: application/json" -H "$AUTH" -d "{\"start_time\":\"${TOMORROW}T10:00:00\"}" > /dev/null && echo "  Slot: ${TOMORROW} 10:00"
    curl -s -X POST "$EXAM_URL/exams/$EXAM1_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":1,"question_type":"mcq","question_text":"Quelle est la derivee de x^2 ?","options":["x","2x","2","x^2"],"correct_answer":"2x","points":5}' > /dev/null && echo "  Q1 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM1_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":2,"question_type":"mcq","question_text":"Que vaut l integrale de 1/x ?","options":["x","ln(x)","1/x^2","e^x"],"correct_answer":"ln(x)","points":5}' > /dev/null && echo "  Q2 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM1_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":3,"question_type":"true_false","question_text":"Pi est un nombre rationnel.","options":["Vrai","Faux"],"correct_answer":"Faux","points":5}' > /dev/null && echo "  Q3 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM1_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":4,"question_type":"mcq","question_text":"Combien vaut 7! (factorielle 7) ?","options":["720","5040","40320","362880"],"correct_answer":"5040","points":5}' > /dev/null && echo "  Q4 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM1_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":5,"question_type":"true_false","question_text":"La somme des angles d un triangle vaut 180 degres.","options":["Vrai","Faux"],"correct_answer":"Vrai","points":5}' > /dev/null && echo "  Q5 added"
else
    echo "  ERROR: $EXAM1"
fi

# --- Exam 2: Informatique ---
echo ""
echo "--- Exam 2: Informatique ---"
EXAM2=$(curl -s -X POST "$EXAM_URL/exams/" -H "Content-Type: application/json" -H "$AUTH" -d "{\"title\":\"Introduction a l Informatique\",\"description\":\"QCM bases de programmation\",\"duration_minutes\":45,\"teacher_id\":\"$TEACHER_ID\"}")
EXAM2_ID=$(echo "$EXAM2" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['exam_id'])" 2>/dev/null || echo "")

if [ -n "$EXAM2_ID" ]; then
    echo "  Created (ID: $EXAM2_ID)"
    curl -s -X POST "$EXAM_URL/exams/$EXAM2_ID/slots" -H "Content-Type: application/json" -H "$AUTH" -d "{\"start_time\":\"${TOMORROW}T14:00:00\"}" > /dev/null && echo "  Slot: ${TOMORROW} 14:00"
    curl -s -X POST "$EXAM_URL/exams/$EXAM2_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":1,"question_type":"mcq","question_text":"Quel langage est interprete ?","options":["C","Java","Python","Rust"],"correct_answer":"Python","points":5}' > /dev/null && echo "  Q1 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM2_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":2,"question_type":"true_false","question_text":"HTML est un langage de programmation.","options":["Vrai","Faux"],"correct_answer":"Faux","points":5}' > /dev/null && echo "  Q2 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM2_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":3,"question_type":"mcq","question_text":"Quelle structure de donnees utilise FIFO ?","options":["Pile","File","Arbre","Graphe"],"correct_answer":"File","points":5}' > /dev/null && echo "  Q3 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM2_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":4,"question_type":"mcq","question_text":"Complexite d une recherche binaire ?","options":["O(n)","O(log n)","O(n^2)","O(1)"],"correct_answer":"O(log n)","points":5}' > /dev/null && echo "  Q4 added"
else
    echo "  ERROR: $EXAM2"
fi

# --- Exam 3: Physique ---
echo ""
echo "--- Exam 3: Physique ---"
EXAM3=$(curl -s -X POST "$EXAM_URL/exams/" -H "Content-Type: application/json" -H "$AUTH" -d "{\"title\":\"Physique Generale\",\"description\":\"Mecanique et thermodynamique\",\"duration_minutes\":90,\"teacher_id\":\"$TEACHER_ID\"}")
EXAM3_ID=$(echo "$EXAM3" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['exam_id'])" 2>/dev/null || echo "")

if [ -n "$EXAM3_ID" ]; then
    echo "  Created (ID: $EXAM3_ID)"
    curl -s -X POST "$EXAM_URL/exams/$EXAM3_ID/slots" -H "Content-Type: application/json" -H "$AUTH" -d "{\"start_time\":\"${TOMORROW}T08:00:00\"}" > /dev/null && echo "  Slot: ${TOMORROW} 08:00"
    curl -s -X POST "$EXAM_URL/exams/$EXAM3_ID/slots" -H "Content-Type: application/json" -H "$AUTH" -d "{\"start_time\":\"${TOMORROW}T14:00:00\"}" > /dev/null && echo "  Slot: ${TOMORROW} 14:00"
    curl -s -X POST "$EXAM_URL/exams/$EXAM3_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":1,"question_type":"mcq","question_text":"Quelle est l unite de la force ?","options":["Watt","Joule","Newton","Pascal"],"correct_answer":"Newton","points":5}' > /dev/null && echo "  Q1 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM3_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":2,"question_type":"true_false","question_text":"La vitesse de la lumiere est environ 300000 km/s.","options":["Vrai","Faux"],"correct_answer":"Vrai","points":5}' > /dev/null && echo "  Q2 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM3_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":3,"question_type":"mcq","question_text":"Qui a formule F = ma ?","options":["Einstein","Newton","Galileo","Bohr"],"correct_answer":"Newton","points":5}' > /dev/null && echo "  Q3 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM3_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":4,"question_type":"true_false","question_text":"L energie cinetique est proportionnelle au carre de la vitesse.","options":["Vrai","Faux"],"correct_answer":"Vrai","points":5}' > /dev/null && echo "  Q4 added"
    curl -s -X POST "$EXAM_URL/exams/$EXAM3_ID/questions/" -H "Content-Type: application/json" -H "$AUTH" -d '{"question_number":5,"question_type":"mcq","question_text":"Premier principe de la thermodynamique ?","options":["Conservation de la masse","Conservation de l energie","Entropie croissante","Equilibre thermique"],"correct_answer":"Conservation de l energie","points":5}' > /dev/null && echo "  Q5 added"
else
    echo "  ERROR: $EXAM3"
fi

# --------------------------------------------------------------------------
# 4. Create a reservation for Alice
# --------------------------------------------------------------------------
echo ""
echo "[4/4] Creating reservation for Alice..."

ALICE_RESP=$(curl -s -X POST "$USER_URL/users/login" -H "Content-Type: application/json" -d '{"email":"alice@student.com","password":"password123"}')
ALICE_TOKEN=$(echo "$ALICE_RESP" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['access_token'])" 2>/dev/null || echo "")
ALICE_ID=$(echo "$ALICE_RESP" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['user']['user_id'])" 2>/dev/null || echo "")

if [ -n "$ALICE_TOKEN" ] && [ -n "$EXAM1_ID" ]; then
    SLOTS=$(curl -s "$EXAM_URL/exams/$EXAM1_ID/slots")
    SLOT_START=$(echo "$SLOTS" | python3 -c "import sys,json; slots=json.loads(sys.stdin.read()); print(slots[0]['start_time'])" 2>/dev/null || echo "")
    if [ -n "$SLOT_START" ]; then
        SLOT_END=$(python3 -c "
from datetime import datetime, timedelta
st = '$SLOT_START'
for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
    try:
        dt = datetime.strptime(st, fmt)
        print((dt + timedelta(minutes=60)).strftime('%Y-%m-%dT%H:%M:%S'))
        break
    except: pass
" 2>/dev/null || echo "")
        if [ -n "$SLOT_END" ]; then
            RES=$(curl -s -X POST "$EXAM_URL/reservations/" -H "Content-Type: application/json" -H "Authorization: Bearer $ALICE_TOKEN" -d "{\"user_id\":\"$ALICE_ID\",\"exam_id\":\"$EXAM1_ID\",\"start_time\":\"$SLOT_START\",\"end_time\":\"$SLOT_END\"}")
            echo "  Reservation: $RES"
        else
            echo "  Could not compute end time"
        fi
    else
        echo "  No slots found for exam 1"
    fi
else
    echo "  Skipping (missing token or exam ID)"
fi

echo ""
echo "=============================="
echo "Fixtures loaded!"
echo "=============================="
echo ""
echo "Test accounts:"
echo "  alice@student.com   / password123 (student)"
echo "  bob@teacher.com     / password123 (teacher)"
echo "  charlie@proctor.com / password123 (proctor)"
echo "  diana@admin.com     / password123 (admin)"
echo ""
echo "Exams created with slots for: $TOMORROW"
echo ""
