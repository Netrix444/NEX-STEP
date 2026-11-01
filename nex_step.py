import streamlit as st
from datetime import datetime, date, time, timedelta

st.set_page_config(page_title="NEX STEP | Decision Assistant", page_icon="⏱️", layout="centered")

st.title("NEX STEP")
st.subheader("Intelligent Decision & Recovery System")
st.write("A question-driven assistant that helps you choose a practical next step when plans go wrong.")
st.caption("Prototype version • Recommendations depend on the answers you provide. Estimates are not guarantees.")

@st.fragment(run_every="30s")
def live_clock():
    now = datetime.now()
    st.metric("Current local time", now.strftime("%I:%M:%S %p"))

live_clock()

SCENARIOS = [
    "Missed transport / running late",
    "Exam tomorrow / syllabus incomplete",
    "Assignment forgotten or incomplete",
    "Missed college or office task / deadline",
]

scenario = st.selectbox("What situation are you facing?", SCENARIOS)

def multi(label, options, help_text=None):
    return st.multiselect(label, options, help=help_text)

def show_plan(title, why, steps, tradeoff, score):
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(f"Suitability score: {score}/100 (rough guide, not a guarantee)")
        st.write(why)
        st.markdown("**Suggested steps**")
        for i, step in enumerate(steps, 1):
            st.write(f"{i}. {step}")
        st.markdown(f"**Trade-off:** {tradeoff}")

def rank_and_show(candidates, priority):
    # Scores are transparent, illustrative weights. They are not predictions.
    weights = {
        "Save time": {"time": 5, "cost": 1, "low_risk": 2, "effect": 3},
        "Spend less money": {"time": 1, "cost": 5, "low_risk": 2, "effect": 3},
        "Reduce risk": {"time": 2, "cost": 1, "low_risk": 5, "effect": 3},
        "Best overall result": {"time": 3, "cost": 2, "low_risk": 3, "effect": 5},
    }
    w = weights[priority]
    ranked = []
    for c in candidates:
        score = (c["time"] * w["time"] + c["cost"] * w["cost"] +
                 c["low_risk"] * w["low_risk"] + c["effect"] * w["effect"])
        score = round(score / (5 * sum(w.values())) * 100)
        ranked.append((score, c))
    ranked.sort(key=lambda x: x[0], reverse=True)
    if not ranked:
        st.warning("There isn't enough information to recommend a plan yet. Review your answers or choose a different option.")
        return
    st.divider()
    st.header("Your recovery options")
    st.write("These options are ranked using your selected priority. Check the requirements before acting.")
    for score, c in ranked[:3]:
        show_plan(c["title"], c["why"], c["steps"], c["tradeoff"], score)
    st.info("Before following a plan, confirm important details such as transport availability, submission rules, costs and deadlines.")

def transport():
    st.header("1. Understand the delay")
    cause = st.radio("Why are you delayed?", ["Overslept", "Regular transport was missed", "Unexpected delay", "Other / not sure"])
    destination = st.text_input("Where do you need to reach? (optional)")
    deadline_time = st.time_input("What time must you reach there?", value=time(9, 0), step=timedelta(minutes=5))
    now = datetime.now()
    deadline_dt = datetime.combine(now.date(), deadline_time)
    remaining = int((deadline_dt - now).total_seconds() // 60)
    if remaining >= 0:
        st.info(f"You have about **{remaining} minutes** until your arrival deadline.")
        if remaining <= 15:
            st.warning("Very little time remains. Prioritise the fastest option you can confirm immediately; do not rely on an unverified departure or arrival estimate.")
    else:
        st.warning(f"That deadline passed about **{abs(remaining)} minutes** ago. Choose a realistic next action and contact the person waiting for you if needed.")
    st.header("2. What is actually available?")
    transport_options = multi("Which options can you genuinely use right now?", ["Bus", "Train/metro", "Auto-rickshaw", "Taxi/cab", "Walk", "Ride from friend/family", "Other"])
    budget = st.number_input("Maximum amount you can spend (₹)", min_value=0, max_value=100000, value=50, step=10)
    know_route = st.radio("Do you know an alternative route?", ["Yes", "No", "Not sure"])
    live_info = st.radio("Can you check live transport / route information?", ["Yes", "No"])
    priority = st.selectbox("What matters most?", ["Save time", "Spend less money", "Reduce risk", "Best overall result"])
    notes = st.text_area("Anything else we should consider? (optional)")
    if st.button("Generate my recovery plans", type="primary"):
        if not transport_options:
            st.error("Select at least one transport option you can actually use.")
            return
        c = []
        if "Auto-rickshaw" in transport_options or "Taxi/cab" in transport_options:
            c.append({"title":"Use a paid ride for the main journey",
                "why":"You selected a paid ride as an available option. Check the fare and estimated arrival before confirming.",
                "steps":["Check the current fare and pickup time in your chosen service or with a driver.","Compare the arrival estimate with your remaining time.","Book only if the fare is within your ₹ budget and the destination is correct."],
                "tradeoff":"Usually costs more; traffic and driver availability can still cause delays.",
                "time":5,"cost":1 if budget < 100 else 3,"low_risk":3,"effect":4})
        if "Bus" in transport_options or "Train/metro" in transport_options:
            c.append({"title":"Check the next public-transport option",
                "why":"Public transport is one of the options you said is available. Verify the next departure rather than assuming a service is running.",
                "steps":["Check the next departure and whether you can reach the stop/station in time.","Confirm the route and any transfer needed.","Use this option only if the arrival estimate meets your deadline."],
                "tradeoff":"Often cheaper, but waiting time, transfers and service delays may reduce reliability.",
                "time":3,"cost":5,"low_risk":3,"effect":3})
        if "Walk" in transport_options:
            c.append({"title":"Walk all or part of the way",
                "why":"Walking is an option you selected. Consider distance, weather, safety and your physical comfort.",
                "steps":["Check the walking distance and estimated time.","If the full walk is too long, check whether a safe partial route is practical.","Choose a well-lit and safe route; do not rush into unsafe conditions."],
                "tradeoff":"Low cost, but may take longer and may not be suitable for long distances.",
                "time":2,"cost":5,"low_risk":2,"effect":2})
        if "Ride from friend/family" in transport_options:
            c.append({"title":"Ask a trusted person for a ride",
                "why":"You indicated that a ride from someone you know may be available.",
                "steps":["Contact them and confirm they are free.","Share your exact destination and required arrival time.","Use this plan only after they confirm."],
                "tradeoff":"Depends on another person's availability and response time.",
                "time":4,"cost":5,"low_risk":4,"effect":4})
        if c:
            rank_and_show(c, priority)
        else:
            st.warning("No plan could be generated from those selections. Add another genuinely available option.")
        if notes: st.write("Additional note considered:", notes)

def exam():
    st.header("1. Understand your exam situation")
    subject = st.text_input("Subject / course name (optional)")
    stop_time = st.time_input("What time do you need to stop studying?", value=(datetime.now() + timedelta(hours=4)).time().replace(second=0, microsecond=0), step=timedelta(minutes=15))
    now = datetime.now()
    stop_dt = datetime.combine(now.date(), stop_time)
    if stop_dt <= now:
        stop_dt += timedelta(days=1)
    hours = max(0.0, (stop_dt - now).total_seconds() / 3600)
    st.info(f"Available study time: **{hours:.1f} hours** (until {stop_dt.strftime('%I:%M %p')}).")
    coverage = st.selectbox("How much of the syllabus is still left?", ["Less than 25%", "25–50%", "50–75%", "Almost everything"])
    topics = multi("What kind of topics remain?", ["Important topics", "Easy topics", "Difficult topics", "Long-answer topics", "Numerical problems", "Topics never studied"])
    resources = multi("Which study resources do you actually have?", ["Class notes", "Previous-year questions", "Textbook", "YouTube / online lectures", "Friends' notes", "Teacher's important questions"])
    restrictions = multi("What limits your study time?", ["Need to sleep", "College/classes", "Gym or other commitments", "No internet", "No major restrictions"])
    goal = st.selectbox("Your main goal", ["Score as high as possible", "Just pass", "Understand concepts", "Cover maximum syllabus"])
    priority = st.selectbox("What matters most right now?", ["Best overall result", "Save time", "Reduce risk", "Spend less money"])
    if st.button("Generate my study recovery plans", type="primary"):
        plans = []
        if hours >= 3:
            steps = ["List the remaining topics and mark the ones your teacher emphasised.","Start with high-importance topics you can realistically complete.","Use the resources you selected; practise questions instead of only rereading.","Keep the final part of your study time for a quick revision."]
            if "Previous-year questions" in resources: steps.insert(2, "Use previous-year questions to identify recurring question styles.")
            if "Teacher's important questions" in resources: steps.insert(2, "Prioritise the teacher's important questions, without assuming they are the only exam content.")
            plans.append({"title":"Priority-first focused study","why":"This plan uses your available study time to focus on high-value topics before trying to cover everything.",
                "steps":steps,"tradeoff":"Some lower-priority topics may remain uncovered.","time":4,"cost":5,"low_risk":4,"effect":5})
        if "Easy topics" in topics or "Important topics" in topics:
            plans.append({"title":"Secure achievable marks first","why":"Begin with topics that are important and/or manageable, based on the topic types you selected.",
                "steps":["Choose a small set of important, manageable topics.","Learn the key definitions, formulas or answer structures.","Solve a few questions without looking at the notes.","Move to the next topic only after checking what you remember."],
                "tradeoff":"Difficult topics may receive less time.","time":4,"cost":5,"low_risk":4,"effect":4})
        if resources:
            plans.append({"title":"Resource-based revision","why":"This plan is built around the study materials you confirmed you have.",
                "steps":["Choose one main source for each topic to avoid switching constantly.","Use notes or textbook for understanding.","Use question papers or practice questions if available.","Write a short summary of key points for final revision."],
                "tradeoff":"The quality and completeness of the available resources affect the result.","time":3,"cost":5,"low_risk":4,"effect":4})
        if hours < 3 or coverage in ["50–75%", "Almost everything"]:
            plans.append({"title":"Protect sleep and make a realistic shortlist","why":"Trying to finish a very large syllabus in very little time can reduce recall and increase exhaustion.",
                "steps":["Select the topics with the highest importance and realistic completion time.","Set a fixed stop time so you get some sleep.","Revise what you completed rather than starting many new topics at the last minute.","If appropriate, ask your teacher or classmates to clarify the most important areas."],
                "tradeoff":"You may not finish the full syllabus; this plan aims for a more controlled preparation.","time":4,"cost":5,"low_risk":5,"effect":4})
        rank_and_show(plans, priority)
        st.caption(f"Your answers: {coverage} remaining; {hours:g} study hours; goal: {goal}.")
        if subject: st.write("Subject:", subject)
        if restrictions: st.write("Restrictions considered:", ", ".join(restrictions))
        if not resources: st.warning("You selected no study resources. The plans are general; add resources you actually have for more useful suggestions.")

def assignment():
    st.header("1. Assignment details")
    subject = st.text_input("Subject / course")
    deadline_date = st.date_input("Assignment due date", value=date.today())
    deadline_time = st.time_input("Assignment due time", value=time(23, 59), step=timedelta(minutes=5))
    deadline = datetime.combine(deadline_date, deadline_time)
    completion = st.slider("How much is already completed?", 0, 100, 30, format="%d%%")
    remaining = multi("What remains to be done?", ["Research", "Writing answers", "Coding / practical work", "Diagrams / calculations", "Formatting", "Printing / uploading"])
    rules = multi("What submission methods are allowed? Select only confirmed methods.", ["Online upload", "Printed copy", "Email to teacher", "In-person submission", "Not sure"])
    resources = multi("What do you currently have?", ["Question sheet / instructions", "Reference notes", "Laptop / computer", "Internet", "Partner / group members"])
    extension = st.radio("Have you confirmed that an extension can be requested?", ["Yes", "No", "Not sure"])
    priority = st.selectbox("What matters most?", ["Save time", "Best overall result", "Reduce risk", "Spend less money"])
    if st.button("Generate my assignment recovery plans", type="primary"):
        plans = []
        if completion > 0:
            plans.append({"title":"Finish and submit the completed work properly","why":"You have already completed part of the assignment. Protect that work and focus on the remaining required parts.",
                "steps":["Check the original instructions and mark mandatory sections.","Complete the highest-priority missing sections first.","Proofread names, calculations, file format and required attachments.","Submit using a method you confirmed is allowed and keep proof of submission."],
                "tradeoff":"A rushed finish may need careful proofreading.","time":4,"cost":5,"low_risk":5,"effect":5})
        if "Online upload" in rules or "Email to teacher" in rules:
            plans.append({"title":"Prepare a clean digital submission","why":"You selected a digital method as allowed. Follow the exact instructions for that method.",
                "steps":["Save the work in the required file format.","Check that the file opens and contains all required pages.","Upload or email it using the confirmed instructions.","Save the confirmation or sent message."],
                "tradeoff":"Only suitable if digital submission is accepted for this assignment.","time":4,"cost":5,"low_risk":4,"effect":4})
        if "Printed copy" in rules or "In-person submission" in rules:
            plans.append({"title":"Prepare the physical submission","why":"You selected a physical submission method as allowed.",
                "steps":["Check whether printing and binding are required.","Confirm where and when the work must be handed in.","Print the final checked version.","Keep a copy or photo for your records."],
                "tradeoff":"Requires access to printing and the correct submission location.","time":3,"cost":3,"low_risk":4,"effect":4})
        if extension in ["Yes", "Not sure"]:
            plans.append({"title":"Ask the teacher about an extension or partial submission","why":"You indicated that an extension may be possible or you are unsure. This is a request, not an assumed permission.",
                "steps":["Contact the teacher politely as early as possible.","Explain briefly what is complete and what remains.","Ask whether an extension or partial submission is permitted.","Follow the teacher's actual response and instructions."],
                "tradeoff":"Approval is not guaranteed; do not treat the deadline as changed until confirmed.","time":4,"cost":5,"low_risk":3,"effect":3})
        rank_and_show(plans, priority)
        if not rules or "Not sure" in rules:
            st.warning("Submission rules are not fully confirmed. Check the official instructions or ask the teacher before choosing a submission method.")
        if subject: st.write("Subject:", subject)
        st.write("Deadline:", deadline.strftime("%d %b %Y, %I:%M %p"))
        if remaining: st.write("Remaining work:", ", ".join(remaining))
        if not resources: st.caption("No resources were selected. The plans do not assume you have any particular materials.")

def task():
    st.header("1. Understand the missed task")
    task_name = st.text_input("What task or responsibility was missed?")
    has_deadline = st.checkbox("I know the original deadline")
    deadline = None
    if has_deadline:
        deadline_date = st.date_input("Original deadline date", value=date.today(), key="task_deadline_date")
        deadline_time = st.time_input("Original deadline time", value=time(17, 0), step=timedelta(minutes=5), key="task_deadline_time")
        deadline = datetime.combine(deadline_date, deadline_time)
    status = st.selectbox("Current status", ["Not started", "Partially completed", "Completed but not submitted", "Submitted late"])
    impact = st.selectbox("What could happen if it remains incomplete?", ["Minor inconvenience", "Marks / evaluation affected", "Work or team affected", "Important official consequence", "Not sure"])
    available = multi("What can you do now?", ["Complete the task", "Contact the responsible person", "Ask a teammate for an update", "Access the required files / system", "Request more time", "None of these confirmed"])
    constraints = multi("What constraints apply?", ["Limited time", "No access to laptop / internet", "Waiting for someone else", "Need approval", "No major constraints"])
    priority = st.selectbox("What matters most?", ["Best overall result", "Save time", "Reduce risk", "Spend less money"])
    if st.button("Generate my task recovery plans", type="primary"):
        plans = []
        if "Complete the task" in available:
            plans.append({"title":"Complete the highest-priority part first","why":"You confirmed that you can work on the task now.",
                "steps":["Open the task instructions and identify the required outcome.","Break the remaining work into small steps.","Complete the most important required part first.","Check the result and submit or report completion through the proper channel."],
                "tradeoff":"May require focusing on this task ahead of less urgent work.","time":4,"cost":5,"low_risk":4,"effect":5})
        if "Contact the responsible person" in available:
            plans.append({"title":"Communicate early and clarify the next action","why":"You said you can contact the person responsible. Early communication can prevent confusion.",
                "steps":["Send a brief, honest update about the missed task.","State what is complete and what remains.","Ask what action is expected now and whether any revised deadline applies.","Follow the response; do not assume an extension has been granted."],
                "tradeoff":"The other person may not respond immediately or approve a change.","time":4,"cost":5,"low_risk":5,"effect":4})
        if "Ask a teammate for an update" in available:
            plans.append({"title":"Coordinate with a teammate","why":"You indicated that a teammate can be contacted.",
                "steps":["Ask what has already been completed and what remains.","Confirm your own responsibility rather than duplicating work.","Agree on a realistic next step and communicate progress."],
                "tradeoff":"Depends on teammate availability and accurate information.","time":3,"cost":5,"low_risk":4,"effect":4})
        if "Request more time" in available:
            plans.append({"title":"Request a revised deadline","why":"You selected this as an action you can take. Approval must be confirmed.",
                "steps":["Explain the situation briefly and respectfully.","Give a realistic completion estimate.","Ask whether a revised deadline is possible.","Continue working unless approval is explicitly given."],
                "tradeoff":"A revised deadline is not guaranteed.","time":4,"cost":5,"low_risk":3,"effect":3})
        rank_and_show(plans, priority)
        if task_name: st.write("Task:", task_name)
        if deadline: st.write("Original deadline:", deadline.strftime("%d %b %Y, %I:%M %p"))
        st.caption(f"Status: {status}. Potential impact: {impact}.")
        if not available or "None of these confirmed" in available:
            st.warning("No practical action was confirmed. First identify who can clarify the task and what resources or permissions are available.")

if scenario == SCENARIOS[0]:
    transport()
elif scenario == SCENARIOS[1]:
    exam()
elif scenario == SCENARIOS[2]:
    assignment()
else:
    task()

st.divider()
st.caption("NEX STEP is an educational prototype, not an emergency service or a substitute for official instructions. Always verify real-world details before acting.")
