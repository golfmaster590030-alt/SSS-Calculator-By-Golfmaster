
import streamlit as st
import numpy_financial as npf

# -----------------------------------------
# ตั้งค่าหน้าเว็บ
# -----------------------------------------
st.set_page_config(
    page_title="FWD Super Smart Savings Calculator",
    page_icon="📊",
    layout="wide",
)

st.title("📊 SSS Calculator By Golfmaster V1.0")
st.subheader("โปรแกรมคำนวณผลประโยชน์และสิทธิลดหย่อนภาษี")

st.info(
    "เครื่องมือจำลองผลประโยชน์ตามสมมติฐานที่ผู้ใช้กำหนด "
    "ไม่ใช่ใบเสนอขายหรือการรับประกันผลตอบแทนจากบริษัทประกัน"
)


# -----------------------------------------
# ส่วนกรอกข้อมูล — แสดงบนหน้าหลัก
# -----------------------------------------
st.subheader("⚙️ กำหนดข้อมูลสำหรับคำนวณ")

col1, col2, col3, col4 = st.columns(4)

with col1:
    plan_years = st.selectbox(
        "แผนชำระเบี้ยประกัน",
        options=[7, 15],
        format_func=lambda x: f"ชำระ {x} ปี",
    )

with col2:
    default_premium = 150000.0 if plan_years == 7 else 70000.0

    premium_per_year = st.number_input(
        "เบี้ยประกันต่อปี (บาท)",
        min_value=1000.0,
        max_value=100_000_000.0,
        value=default_premium,
        step=10000.0,
    )

with col3:
    tax_bracket = st.selectbox(
        "อัตราภาษี (%)",
        options=[0, 5, 10, 15, 20, 25, 30, 35],
        index=2,
    )

with col4:
    custom_index_rate = st.number_input(
        "ผลตอบแทนสมมติจากดัชนี (%)",
        min_value=0.0,
        max_value=100.0,
        value=4.0,
        step=0.5,
    )

calculate = st.button(
    "🧮 คำนวณผลประโยชน์",
    type="primary",
    use_container_width=True,
)


# -----------------------------------------
# ฟังก์ชันคำนวณ
# -----------------------------------------
def calculate_plan(
    plan_years,
    premium_per_year,
    tax_bracket,
    custom_index_rate,
):
    total_protection_years = 25

    total_paid_premium = premium_per_year * plan_years

    # สมมติฐานสิทธิลดหย่อนภาษี
    eligible_tax_base = min(premium_per_year, 100_000.0)
    tax_saved_per_year = eligible_tax_base * tax_bracket / 100
    total_tax_saved = tax_saved_per_year * plan_years

    net_premium_outflow = (
        total_paid_premium - total_tax_saved
    )

    # ผลประโยชน์การันตีตามสูตรต้นฉบับ
    if plan_years == 7:
        total_guaranteed_received = (
            premium_per_year * 0.01 * 24
            + premium_per_year * 7.00
        )
        checkpoint_year = 7
        base_checkpoint_bonus = (
            165848 * premium_per_year / 150000
        )
        base_year25_bonus = (
            874545 * premium_per_year / 150000
        )
    else:
        total_guaranteed_received = (
            premium_per_year * 0.01 * 24
            + premium_per_year * 14.80
        )
        checkpoint_year = 15
        base_checkpoint_bonus = (
            420473 * premium_per_year / 70000
        )
        base_year25_bonus = (
            874545 * premium_per_year / 70000
        )

    # โบนัสสมมติตามอัตราดัชนี
    index_rate = custom_index_rate / 100
    scale_factor = index_rate / 0.04

    checkpoint_bonus = base_checkpoint_bonus * scale_factor
    year25_bonus = base_year25_bonus * scale_factor

    total_index_bonus = checkpoint_bonus + year25_bonus

    total_benefits_all = (
        total_guaranteed_received + total_index_bonus
    )

    net_profit = (
        total_benefits_all
        + total_tax_saved
        - total_paid_premium
    )

    # กระแสเงินสดสำหรับคำนวณ IRR
    cash_flows = [
        -(premium_per_year - tax_saved_per_year)
        if year <= plan_years
        else 0.0
        for year in range(1, total_protection_years + 1)
    ]

    for year in range(1, total_protection_years + 1):

        # เงินคืน 1% ในปีที่ 1-24
        if year <= 24:
            cash_flows[year - 1] += premium_per_year * 0.01

        # เงินคืนการันตีส่วนที่เหลือในปีที่ 25
        if year == 25:
            cash_flows[year - 1] += (
                total_guaranteed_received
                - premium_per_year * 0.01 * 24
            )

        # โบนัสตามสมมติฐาน
        if year == checkpoint_year:
            cash_flows[year - 1] += checkpoint_bonus

        if year == 25:
            cash_flows[year - 1] += year25_bonus

    try:
        irr_result = npf.irr(cash_flows)
        irr_value = (
            float(irr_result) * 100
            if irr_result is not None
            and irr_result == irr_result
            else None
        )
    except (ValueError, OverflowError, ZeroDivisionError):
        irr_value = None

    return {
        "total_paid_premium": total_paid_premium,
        "total_tax_saved": total_tax_saved,
        "net_premium_outflow": net_premium_outflow,
        "total_guaranteed_received": total_guaranteed_received,
        "checkpoint_year": checkpoint_year,
        "checkpoint_bonus": checkpoint_bonus,
        "year25_bonus": year25_bonus,
        "total_index_bonus": total_index_bonus,
        "total_benefits_all": total_benefits_all,
        "net_profit": net_profit,
        "irr_value": irr_value,
        "cash_flows": cash_flows,
    }


def baht(value):
    return f"{value:,.2f} บาท"


# -----------------------------------------
# แสดงผลลัพธ์
# -----------------------------------------
if calculate:
    result = calculate_plan(
        plan_years,
        premium_per_year,
        tax_bracket,
        custom_index_rate,
    )

    st.divider()
    st.header(f"สรุปผลแผน 25/{plan_years}")

    # ตัวเลขสำคัญ
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "เบี้ยประกันรวม",
        baht(result["total_paid_premium"]),
    )

    col2.metric(
        "ประหยัดภาษีตามสมมติฐาน",
        baht(result["total_tax_saved"]),
    )

    col3.metric(
        "ต้นทุนสุทธิหลังหักภาษี",
        baht(result["net_premium_outflow"]),
    )

    st.divider()

    # ผลประโยชน์
    st.subheader("💰 รายละเอียดผลประโยชน์")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ผลประโยชน์การันตี")
        st.metric(
            "เงินคืนการันตีรวม",
            baht(result["total_guaranteed_received"]),
        )

        st.caption(
            "ตัวเลขนี้คำนวณจากสูตรที่ระบุในโปรแกรม "
            "ควรตรวจสอบกับเอกสารผลประโยชน์ของกรมธรรม์"
        )

    with col2:
        st.markdown("#### ผลประโยชน์ไม่การันตี")

        st.metric(
            f"โบนัสปีที่ {result['checkpoint_year']}",
            baht(result["checkpoint_bonus"]),
        )

        st.metric(
            "โบนัสปีที่ 25",
            baht(result["year25_bonus"]),
        )

        st.metric(
            "โบนัสไม่การันตีรวม",
            baht(result["total_index_bonus"]),
        )

    st.divider()

    # สรุปผลตอบแทน
    st.subheader("📈 สรุปผลตอบแทน")

    col1, col2 = st.columns(2)

    col1.metric(
        "ผลประโยชน์รวม",
        baht(result["total_benefits_all"]),
    )

    col2.metric(
        "กำไรสุทธิรวมประโยชน์ภาษี",
        baht(result["net_profit"]),
    )

    if result["irr_value"] is not None:
        st.metric(
            "IRR ต่อปี หลังหักภาษีตามสมมติฐาน",
            f"{result['irr_value']:.2f}%",
        )
    else:
        st.warning(
            "ไม่สามารถหา IRR ที่เหมาะสมจากกระแสเงินสดชุดนี้ได้"
        )

    st.caption(
        f"สมมติอัตราผลตอบแทนจากดัชนี {custom_index_rate:.2f}% ต่อปี "
        f"และอัตราภาษี {tax_bracket}%"
    )

    # ตารางกระแสเงินสด
    with st.expander("ดูตารางกระแสเงินสดสำหรับคำนวณ IRR"):
        import pandas as pd

        cash_flow_df = pd.DataFrame({
            "ปีกรมธรรม์": range(1, 26),
            "กระแสเงินสดสุทธิ (บาท)": result["cash_flows"],
        })

        st.dataframe(
            cash_flow_df.style.format({
                "กระแสเงินสดสุทธิ (บาท)": "{:,.2f}"
            }),
            use_container_width=True,
            hide_index=True,
        )

else:
    st.markdown("### เริ่มต้นใช้งาน")
    st.write(
        "เลือกแผนชำระเบี้ย ระบุเบี้ยประกัน อัตราภาษี "
        "และผลตอบแทนสมมติจากดัชนีที่แถบด้านซ้าย "
        "จากนั้นกดปุ่ม **คำนวณผลประโยชน์**"
    )

st.divider()

st.caption(
    "ข้อควรระวัง: การลดหย่อนภาษีขึ้นอยู่กับคุณสมบัติของกรมธรรม์ "
    "เงื่อนไขตามกฎหมาย และสิทธิที่ผู้เอาประกันยังมีอยู่จริง "
    "โบนัสที่อ้างอิงดัชนีเป็นสมมติฐาน ไม่ใช่ผลตอบแทนการันตี "
    "โปรดตรวจสอบเอกสารเสนอขายและเงื่อนไขกรมธรรม์ฉบับจริงก่อนนำเสนอ"
)
