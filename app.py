
import streamlit as st
import numpy_financial as npf
import pandas as pd
import math

st.set_page_config(
    page_title="FWD Super Smart Savings",
    page_icon="📊",
    layout="wide",
)

st.title("📊 SSS Calculator By GOLFMASTER")
st.subheader("เครื่องคำนวณผลประโยชน์แผน 25/7 และ 25/15")

st.caption(
    "เครื่องมือจำลองผลประโยชน์จากข้อมูลที่ระบุ "
    "โปรดตรวจสอบกับเอกสารผลประโยชน์กรมธรรม์ฉบับจริง"
)

# ==================================================
# ตารางโบนัสอ้างอิงจากภาพแผน 25/7
# ==================================================
BONUS_25_7 = {
    2.0: {
        "checkpoint": 78068,
        "year25": 336315,
    },
    4.0: {
        "checkpoint": 165848,
        "year25": 874545,
    },
    6.0: {
        "checkpoint": 264390,
        "year25": 1728248,
    },
}

# โบนัสฐานแผน 25/15 จากโค้ดต้นฉบับ
# ยืนยันได้เพียงค่าฐานที่ 4% ตามสมมติฐานเดิม
BONUS_25_15 = {
    4.0: {
        "checkpoint": 420473,
        "year25": 874545,
    }
}


def money(value):
    return f"{value:,.2f} บาท"


def calculate_plan(
    plan_years,
    premium,
    tax_rate,
    index_rate,
    use_tax,
):
    # ----------------------------------------------
    # 1. เบี้ยประกันและภาษี
    # ----------------------------------------------
    protection_years = 25
    total_premium = premium * plan_years

    # สมมติฐานเดิม: เบี้ยที่เข้าเกณฑ์ลดหย่อนสูงสุด 100,000/ปี
    eligible_premium = min(premium, 100000)
    tax_saved_per_year = eligible_premium * tax_rate / 100

    total_tax_saved = (
        tax_saved_per_year * plan_years
        if use_tax
        else 0.0
    )

    net_cost = total_premium - total_tax_saved

    # ----------------------------------------------
    # 2. ผลประโยชน์การันตีตามสูตรเดิม
    # ต้องตรวจสอบกับเอกสารกรมธรรม์
    # ----------------------------------------------
    if plan_years == 7:
        checkpoint_year = 7
        guaranteed_total = premium * 0.01 * 24 + premium * 7.00
        bonus_table = BONUS_25_7
        reference_base = 150000
    else:
        checkpoint_year = 15
        guaranteed_total = premium * 0.01 * 24 + premium * 14.80
        bonus_table = BONUS_25_15
        reference_base = 70000

    # ----------------------------------------------
    # 3. โบนัสอ้างอิง
    # รองรับเฉพาะระดับดัชนีที่มีข้อมูล
    # ----------------------------------------------
    if index_rate not in bonus_table:
        return {
            "error": (
                f"ยังไม่มีตารางโบนัสอ้างอิงสำหรับแผน 25/{plan_years} "
                f"ที่ดัชนี {index_rate:.1f}% "
                "กรุณาใช้ระดับดัชนีที่รองรับ หรือเพิ่มข้อมูลจาก "
                "เอกสารผลประโยชน์จริงก่อนคำนวณ"
            )
        }

    reference = bonus_table[index_rate]

    # ปรับจำนวนโบนัสตามสัดส่วนเบี้ย
    # ใช้ได้เมื่อโครงสร้างผลิตภัณฑ์รองรับการแปรผันแบบสัดส่วน
    scale = premium / reference_base

    checkpoint_bonus = reference["checkpoint"] * scale
    year25_bonus = reference["year25"] * scale

    total_index_bonus = checkpoint_bonus + year25_bonus
    total_benefits = guaranteed_total + total_index_bonus

    profit = total_benefits + total_tax_saved - total_premium

    # ----------------------------------------------
    # 4. กระแสเงินสดรายปี
    # ----------------------------------------------
    cash_flows_before_tax = []
    cash_flows_after_tax = []

    for year in range(1, protection_years + 1):
        # เบี้ยที่จ่ายในแต่ละปี
        premium_outflow = premium if year <= plan_years else 0.0

        # เงินคืน 1% ในปี 1-24
        inflow = premium * 0.01 if year <= 24 else 0.0

        # ปีที่ 25 รับส่วนที่เหลือของเงินคืนการันตี
        if year == 25:
            inflow += guaranteed_total - premium * 0.01 * 24

        # โบนัสตามตาราง
        if year == checkpoint_year:
            inflow += checkpoint_bonus

        if year == 25:
            inflow += year25_bonus

        cash_flows_before_tax.append(inflow - premium_outflow)

        tax_benefit = (
            tax_saved_per_year
            if use_tax and year <= plan_years
            else 0.0
        )

        cash_flows_after_tax.append(
            inflow - premium_outflow + tax_benefit
        )

    def safe_irr(flows):
        try:
            value = npf.irr(flows)
            if value is None or not math.isfinite(float(value)):
                return None
            return float(value) * 100
        except (ValueError, OverflowError, ZeroDivisionError):
            return None

    irr_before_tax = safe_irr(cash_flows_before_tax)
    irr_after_tax = safe_irr(cash_flows_after_tax)

    return {
        "total_premium": total_premium,
        "total_tax_saved": total_tax_saved,
        "net_cost": net_cost,
        "guaranteed_total": guaranteed_total,
        "checkpoint_year": checkpoint_year,
        "checkpoint_bonus": checkpoint_bonus,
        "year25_bonus": year25_bonus,
        "total_index_bonus": total_index_bonus,
        "total_benefits": total_benefits,
        "profit": profit,
        "irr_before_tax": irr_before_tax,
        "irr_after_tax": irr_after_tax,
        "cash_flows": cash_flows_after_tax,
    }


def show_irr(label, value):
    if value is None:
        st.metric(label, "คำนวณไม่ได้")
    else:
        st.metric(label, f"{value:.2f}% ต่อปี")


# ==================================================
# 5. แบบฟอร์มบนหน้าหลัก
# ==================================================
st.markdown("### ⚙️ กำหนดข้อมูล")

c1, c2, c3, c4 = st.columns(4)

with c1:
    plan_years = st.selectbox(
        "แผนชำระเบี้ย",
        [7, 15],
        format_func=lambda x: f"25/{x}",
        key="plan_years",
    )

with c2:
    default_premium = 150000.0 if plan_years == 7 else 70000.0

    premium = st.number_input(
        "เบี้ยประกันต่อปี (บาท)",
        min_value=1000.0,
        max_value=100000000.0,
        value=default_premium,
        step=10000.0,
        key=f"premium_{plan_years}",
    )

with c3:
    tax_rate = st.selectbox(
        "อัตราภาษีส่วนเพิ่ม (%)",
        [0, 5, 10, 15, 20, 25, 30, 35],
        index=2,
    )

with c4:
    available_rates = (
        [2.0, 4.0, 6.0]
        if plan_years == 7
        else [4.0]
    )

    index_rate = st.selectbox(
        "ระดับดัชนีอ้างอิง (%)",
        available_rates,
        format_func=lambda x: f"+{x:.0f}%",
    )

use_tax = st.checkbox(
    "รวมประโยชน์จากการลดหย่อนภาษีในการคำนวณ IRR",
    value=True,
)

st.caption(
    "แผน 25/7 รองรับดัชนี +2%, +4%, +6% ตามภาพอ้างอิง "
    "ส่วนแผน 25/15 ใช้ค่าฐาน +4% จากโค้ดเดิมเท่านั้น"
)

calculate = st.button(
    "🧮 คำนวณผลประโยชน์",
    type="primary",
    use_container_width=True,
)

# ==================================================
# 6. แสดงผล
# ==================================================
if calculate:
    result = calculate_plan(
        plan_years=plan_years,
        premium=premium,
        tax_rate=tax_rate,
        index_rate=index_rate,
        use_tax=use_tax,
    )

    if "error" in result:
        st.error(result["error"])

    else:
        st.divider()
        st.header(f"สรุปผลแผน 25/{plan_years}")

        a, b, c = st.columns(3)

        a.metric("เบี้ยประกันรวม", money(result["total_premium"]))
        b.metric("ประหยัดภาษีโดยประมาณ", money(result["total_tax_saved"]))
        c.metric("ต้นทุนสุทธิหลังภาษี", money(result["net_cost"]))

        st.divider()
        st.subheader("💰 รายละเอียดผลประโยชน์")

        a, b = st.columns(2)

        with a:
            st.markdown("#### ผลประโยชน์การันตี")
            st.metric(
                "เงินคืนการันตีรวม",
                money(result["guaranteed_total"]),
            )

        with b:
            st.markdown("#### ผลประโยชน์ไม่การันตี")
            st.metric(
                f"โบนัสปีที่ {result['checkpoint_year']}",
                money(result["checkpoint_bonus"]),
            )
            st.metric(
                "โบนัสปีที่ 25",
                money(result["year25_bonus"]),
            )
            st.metric(
                "โบนัสรวม",
                money(result["total_index_bonus"]),
            )

        st.divider()
        st.subheader("📈 สรุปผลตอบแทน")

        a, b = st.columns(2)

        a.metric(
            "ผลประโยชน์รวม",
            money(result["total_benefits"]),
        )
        b.metric(
            "กำไรสุทธิรวมประโยชน์ภาษี",
            money(result["profit"]),
        )

        a, b = st.columns(2)

        show_irr("IRR ก่อนภาษี", result["irr_before_tax"])
        show_irr("IRR หลังภาษีตามสมมติฐาน", result["irr_after_tax"])

        with st.expander("📋 ตารางกระแสเงินสดรายปี"):
            df = pd.DataFrame({
                "ปีกรมธรรม์": range(1, 26),
                "กระแสเงินสดสุทธิ (บาท)": result["cash_flows"],
            })

            st.dataframe(
                df.style.format({
                    "กระแสเงินสดสุทธิ (บาท)": "{:,.2f}"
                }),
                use_container_width=True,
                hide_index=True,
            )

        st.warning(
            "ตัวเลขเป็นการจำลองจากสูตรและข้อมูลที่ใส่ไว้ในโปรแกรม "
            "ไม่ใช่การยืนยันผลประโยชน์จากบริษัทประกัน "
            "โดยเฉพาะแผน 25/15 และการปรับโบนัสตามจำนวนเบี้ย "
            "ควรตรวจสอบกับตารางผลประโยชน์ฉบับจริง"
        )

else:
    st.info(
        "เลือกแผน กรอกเบี้ยและอัตราภาษี จากนั้นกด "
        "คำนวณผลประโยชน์ เพื่อแสดงผลลัพธ์"
    )

st.divider()
st.caption(
    "หมายเหตุ: สิทธิภาษีขึ้นอยู่กับเงื่อนไขกรมธรรม์ "
    "สิทธิที่ผู้เอาประกันมีอยู่จริง และกฎหมายภาษีที่ใช้บังคับ"
)
