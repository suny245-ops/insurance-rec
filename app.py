# app.py
# 실행: pip install streamlit && streamlit run app.py

import streamlit as st
from typing import List, Dict, Tuple

st.set_page_config(page_title="설계사용 상품추천 데모", page_icon="🧭")

# 1) 보장 태그 정의 (표시=한글, 내부태그=영문)
NEED_LABELS = [
    ("사망", "death"),
    ("연금", "annuity"),
    ("일반암", "cancer_general"),
    ("소액암", "cancer_minor"),
    ("뇌", "brain"),
    ("심", "heart"),
    ("수술", "surgery"),
    ("골절", "fracture"),
]
LABEL_TO_TAG = {ko: en for ko, en in NEED_LABELS}
TAG_TO_LABEL = {en: ko for ko, en in NEED_LABELS}

# 2) 예시 상품 10개
PRODUCTS: List[Dict] = [
    dict(product_id="SL-TERM-20", name="Prime Term 20y", product_type="term_life",
         min_age=20, max_age=70, gender="Any",
         needs_tags=["death"], notes="표준 사망보장"),
    dict(product_id="SL-ANN-FIX", name="Fixed Annuity 10y", product_type="annuity",
         min_age=30, max_age=80, gender="Any",
         needs_tags=["annuity"], notes="연금수령 중점"),
    dict(product_id="SL-CAN-ESS", name="Cancer Essential", product_type="cancer",
         min_age=20, max_age=79, gender="Any",
         needs_tags=["cancer_general", "surgery"], notes="일반암 중심"),
    dict(product_id="SL-CAN-LITE", name="Cancer Lite", product_type="cancer",
         min_age=20, max_age=79, gender="Any",
         needs_tags=["cancer_minor"], notes="소액암 특화"),
    dict(product_id="SL-BRAIN", name="Brain Guard", product_type="ci_brain",
         min_age=25, max_age=75, gender="Any",
         needs_tags=["brain", "surgery"], notes="뇌 관련 보장"),
    dict(product_id="SL-HEART", name="Heart Shield", product_type="ci_heart",
         min_age=25, max_age=75, gender="Any",
         needs_tags=["heart", "surgery"], notes="심장 관련 보장"),
    dict(product_id="SL-SURGERY", name="Surgery Care", product_type="medical",
         min_age=18, max_age=80, gender="Any",
         needs_tags=["surgery"], notes="수술 특화"),
    dict(product_id="SL-FRACTURE", name="Fracture Plan", product_type="accident",
         min_age=18, max_age=80, gender="Any",
         needs_tags=["fracture"], notes="골절 보장"),
    dict(product_id="SL-WH-PLUS", name="Women’s Health Plus", product_type="womens",
         min_age=20, max_age=70, gender="F",
         needs_tags=["cancer_general", "surgery"], notes="여성 특화"),
    dict(product_id="SL-MEN-PRO", name="Men’s Pro Care", product_type="mens",
         min_age=20, max_age=75, gender="M",
         needs_tags=["cancer_general", "surgery"], notes="남성 특화"),
]

# 3) 간단 점수 로직: 보장일치도(0.8) + 연령적합도(0.2)
def eligible(product: Dict, age: int, gender: str) -> Tuple[bool, str]:
    if not (product["min_age"] <= age <= product["max_age"]):
        return False, "가입연령 제외"
    g = product.get("gender", "Any")
    if g != "Any" and g.lower()[0] != gender.lower()[0]:
        return False, "성별 제한"
    return True, "가입가능"

def score_product(product: Dict, age: int, gender: str, desired_tags: List[str]) -> Dict:
    ok, reason = eligible(product, age, gender)
    if not ok:
        return {
            "product_id": product["product_id"],
            "상품명": product["name"],
            "유형": product["product_type"],
            "점수": 0.0,
            "추천 사유": reason,
            "보장 태그": ", ".join(TAG_TO_LABEL.get(t, t) for t in product.get("needs_tags", []))
        }

    tags = set(product.get("needs_tags", []))
    desired = set(desired_tags)
    cov_match = 0.0 if not desired else len(tags & desired) / max(1, len(desired))

    mid = (product["min_age"] + product["max_age"]) / 2.0
    span = max(1.0, (product["max_age"] - product["min_age"]) / 2.0)
    age_fit = max(0.0, 1.0 - abs(age - mid) / span)

    score = 0.8 * cov_match + 0.2 * age_fit

    reasons = []
    if cov_match >= 0.67: reasons.append("보장 일치 높음")
    elif cov_match > 0: reasons.append("보장 일치 보통")
    else: reasons.append("일반 적합")
    if age_fit > 0.6: reasons.append("연령 적합 양호")

    return {
        "product_id": product["product_id"],
        "상품명": product["name"],
        "유형": product["product_type"],
        "점수": round(score, 3),
        "추천 사유": "; ".join(reasons),
        "보장 태그": ", ".join(TAG_TO_LABEL.get(t, t) for t in product.get("needs_tags", []))
    }

# 4) UI
st.title("설계사용 상품추천 프로그램")
st.caption("내 업무에 AI를 더하다 – 단일파일 데모")

col1, col2, col3 = st.columns([1,1,1])
with col1:
    name = st.text_input("이름", value="", placeholder="홍길동")
with col2:
    age = st.number_input("연령", min_value=18, max_value=90, value=60, step=1)
with col3:
    gender = st.radio("성별", options=["M", "F"], horizontal=True, index=1)

st.markdown("필요 보장 선택")
selected_labels: List[str] = st.pills(
    "보장",
    options=[ko for ko, _ in NEED_LABELS],
    selection_mode="multi",
)
desired_tags = [LABEL_TO_TAG[ko] for ko in selected_labels]

topn = st.slider("표시 개수", 1, 10, 5)

st.markdown("---")
st.subheader("추천 결과")

scored = [score_product(p, age, gender, desired_tags) for p in PRODUCTS]
eligible_rows = [r for r in scored if r["점수"] > 0]
eligible_rows.sort(key=lambda x: (-x["점수"], x["상품명"]))

if not eligible_rows:
    st.info("조건에 맞는 추천이 없습니다. 보장을 조정해보세요.")
else:
    # 이름이 있으면 문장 한 줄
    if name.strip():
        st.write(f"{name}님 조건에 따른 추천입니다.")
    # 순위 붙여 표로
    rows = []
    for i, r in enumerate(eligible_rows[:topn], start=1):
        rows.append({
            "순위": i,
            **{k: v for k, v in r.items() if k not in ("product_id",)},
        })
    st.dataframe(rows, hide_index=True, use_container_width=True)

with st.expander("설명"):
    st.write(
        "- 입력: 이름, 연령, 성별, 필요 보장 8종만 사용\n"
        "- 점수: 보장 일치도 0.8 + 연령 적합도 0.2\n"
        "- 실제 적용시 상품·특약·규정 데이터로 확장"
    )
