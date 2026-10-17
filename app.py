import streamlit as st
import numpy_financial as npf

# ตั้งค่าหน้าจอเว็บ
st.set_page_config(page_title="FWD Super Smart Savings Calculator", page_icon="📈", layout="centered")

st.title("📈 คำนวณผลตอบแทน FWD Super Smart Savings By GOLFMASTER")
st.write("โปรแกรมจำลองผลประโยชน์การออมทรัพย์แบบ Index Linked พร้อมคำนวณสิทธิ์ลดหย่อนภาษี")

# ส่วนรับค่า (Sidebar หรือหน้าหลัก)
st.subheader("📝 กรอกข้อมูลแผนประกันของคุณ")

plan = st.selectbox("เลือกแผนชำระเบี้ย", ["25/7 (จ่ายเบี้ย 7 ปี คุ้มครอง 25 ปี)", "25/15 (จ่ายเบี้ย 15 ปี คุ้มครอง 25 ปี)"])
plan_years = 7 if "7" in plan else 15

premium_per_year = st.number_input("จำนวนเงินเบี้ยประกันภัยต่อปี (บาท)", min_value=1000.0, value=150000.0, step=10000.0)
tax_bracket = st.slider("อัตราภาษีเงินได้บุคคลธรรมดาของคุณ (%)", min_value=0.0, max_value=35.0, value=10.0, step=5.0)
custom_index_rate = st.slider("อัตราผลตอบแทนสมมติจากดัชนีอ้างอิงต่อปี (%)", min_value=0.0, max_value=30.0, value=4.0, step=1.0) / 100.0

# ปุ่มกดคำนวณ
if st.button("🚀 คำนวณผลลัพธ์"):
    total_protection_years = 25
    total_paid_premium = premium_per_year * plan_years
    
    # 1. คำนวณภาษี
    eligible_tax_base_per_year = min(premium_per_year, 100000.0)
    tax_saved_per_year = eligible_tax_base_per_year * (tax_bracket / 100.0)
    total_tax_saved = tax_saved_per_year * plan_years
    net_premium_outflow = total_paid_premium - total_tax_saved

    # 2. คำนวณเงินคืนการันตีและโบนัสดัชนี
    if plan_years == 7:
        total_guaranteed_received = (premium_per_year * 0.01 * 24) + (premium_per_year * 7.00)
        checkpoint_year = 7
        base_ref_premium = 150000.0
        scale_ratio = premium_per_year / base_ref_premium
        
        growth_multiplier = ((1 + custom_index_rate) / (1 + 0.04)) ** checkpoint_year
        checkpoint_bonus = 165848 * scale_ratio * growth_multiplier
        
        growth_multiplier_25 = ((1 + custom_index_rate) / (1 + 0.04)) ** total_protection_years
        year25_bonus = 874545 * scale_ratio * growth_multiplier_25
    else:
        total_guaranteed_received = (premium_per_year * 0.01 * 24) + (premium_per_year * 14.80)
        checkpoint_year = 15
        base_ref_premium = 70000.0
        scale_ratio = premium_per_year / base_ref_premium
        
        growth_multiplier = ((1 + custom_index_rate) / (1 + 0.04)) ** checkpoint_year
        checkpoint_bonus = 420473 * scale_ratio * growth_multiplier
        
        growth_multiplier_25 = ((1 + custom_index_rate) / (1 + 0.04)) ** total_protection_years
        year25_bonus = 874545 * scale_ratio * growth_multiplier_25

    total_index_bonus = checkpoint_bonus + year25_bonus
    total_benefits_all = total_guaranteed_received + total_index_bonus
    net_profit = (total_benefits_all + total_tax_saved) - total_paid_premium

    # 3. คำนวณ IRR
    cash_flows = [- (premium_per_year - tax_saved_per_year)] * plan_years + [0] * (total_protection_years - plan_years)
    for yr in range(1, total_protection_years + 1):
        if yr <= 24:
            cash_flows[yr - 1] += (premium_per_year * 0.01)
        if yr == 25:
            cash_flows[yr - 1] += (total_guaranteed_received - (premium_per_year * 0.01 * 24))
        if yr == checkpoint_year:
            cash_flows[yr - 1] += checkpoint_bonus
        if yr == total_protection_years:
            cash_flows[yr - 1] += year25_bonus

    try:
        irr_value = npf.irr(cash_flows) * 100
    except:
        irr_value = 0.0

    # 4. แสดงผลลัพธ์แบบสวยงามบนเว็บ
    st.markdown("---")
    st.subheader("📊 สรุปผลการคำนวณตลอดสัญญา 25 ปี")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="เบี้ยประกันรวมทั้งหมด", value=f"{total_paid_premium:,.2f} ฿")
        st.metric(label="สิทธิลดหย่อนภาษีรวม", value=f"{total_tax_saved:,.2f} ฿")
        st.metric(label="ต้นทุนเบี้ยสุทธิหลังหักภาษี", value=f"{net_premium_outflow:,.2f} ฿")
    with col2:
        st.metric(label="ผลประโยชน์รวมทั้งหมด", value=f"{total_benefits_all:,.2f} ฿")
        st.metric(label="กำไรสุทธิรวมลดหย่อนภาษี", value=f"{net_profit:,.2f} ฿")
        st.metric(label="IRR (ผลตอบแทนเฉลี่ยต่อปี)", value=f"{irr_value:.2f}%")

    st.markdown("---")
    st.info(f"""
    **รายละเอียดผลประโยชน์:**
    - เงินคืนการันตีรวมตลอดสัญญา: **{total_guaranteed_received:,.2f} บาท**
    - โบนัสดัชนีงวดที่ 1 (ปีที่ {checkpoint_year}): **{checkpoint_bonus:,.2f} บาท**
    - โบนัสดัชนีงวดที่ 2 (ปีที่ 25): **{year25_bonus:,.2f} บาท**
    """)
