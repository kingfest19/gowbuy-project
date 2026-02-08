# Real-World Origin Verification Examples

## Example 1: Legitimate iPhone (PASSES ✓)

**Vendor Input:**
```
Product Name: Apple iPhone 14 Pro
Brand: Apple
Manufacturer: Foxconn Electronics
Manufacturer Address: Shenzhen, China
Origin Country: US
Device Identifier Type: IMEI
Device Identifier Value: 357847058947382
Certification Numbers: FCC ID: 2AOKB-A2896
Price: $999.99
Authenticity Status: Authentic
Category: Electronics
```

**Verification Analysis:**
```
1. Brand Check (Apple → US): ✓ MATCH
   - Apple is a US company
   
2. Manufacturer Check:
   - Foxconn manufactures iPhones in China ✓
   - Manufactured in China but designed/distributed from US ✓
   
3. Device Identifier Check:
   - IMEI prefix "357" → Ericsson (doesn't determine country for phones)
   - But IMEI format is valid ✓
   
4. Certification Check:
   - FCC ID (Federal Communications Commission) = USA ✓
   
5. Price Check:
   - $999.99 is reasonable for premium US-origin phone ✓
   
6. Category Check:
   - Electronics from US is common ✓
```

**Result:**
```
✓ VALID
Score: 92/100
Confidence: 95%
Reasoning: Origin claim of US appears legitimate. Brand matches 
           origin, certifications are US-based, price is appropriate 
           for premium device.
Action: Product can go live immediately
```

---

## Example 2: Suspicious Counterfeit Luxury Watch (FAILS 🚩)

**Vendor Input:**
```
Product Name: Premium Rolex Submarine
Brand: Rolex
Manufacturer: (left blank)
Manufacturer Address: (left blank)
Origin Country: US
Device Identifier Type: Serial Number
Device Identifier Value: AB123456
Certification Numbers: (left blank)
Price: $49.99
Authenticity Status: Unknown
Category: Luxury Watches
```

**Verification Analysis:**
```
1. Brand Check (Rolex → Switzerland):
   ✗ MISMATCH - Rolex is Swiss, not US
   - Detects mismatch: "Brand 'Rolex' typically from CH, not US"
   
2. Manufacturer Check:
   - Empty fields = No verification data available ✗
   
3. Certification Check:
   - No certifications provided
   - Luxury watches typically have certificates of authenticity ✗
   
4. Price Check:
   - $49.99 is EXTREMELY low for authentic Rolex ✗
   - Rolex watches cost minimum $5000+
   - Typical Rolex price range: $5000-$50000+
   - This extreme price difference indicates counterfeit
   
5. Authenticity Check:
   - Status is "Unknown" for a luxury item
   - Luxury items should have "Authentic" or "Refurbished" ✗
   
6. Category Check:
   - Luxury watches from US are uncommon ✗
   - Switzerland, Japan more typical
```

**Detected Mismatches:**
- Brand 'Rolex' typically from Switzerland, not USA
- Device Serial Number format doesn't match Rolex patterns
- No authenticity certifications provided
- Extreme price mismatch for claimed luxury brand

**Result:**
```
🚩 HIGHLY SUSPICIOUS
Score: 12/100
Confidence: 5%
Severity: CRITICAL

Reasoning: Multiple red flags detected:
1. Brand claims from wrong country (Rolex is Swiss)
2. Extreme price undercut ($49.99 vs $5000+ for real Rolex)
3. No authenticity documentation
4. Missing manufacturer information

Suggested Origin: China (likely counterfeit)

Admin Action Required: 
- ⚠️ BLOCK PRODUCT from going live
- Flag vendor for possible counterfeiting
- Request authenticity certificates or proof of purchase
- Recommended: Contact Rolex to verify if authorized seller
```

---

## Example 3: Valid Chinese Electronics (PASSES ✓)

**Vendor Input:**
```
Product Name: Xiaomi Mi 13 Smartphone
Brand: Xiaomi
Manufacturer: Xiaomi Corporation
Manufacturer Address: 1 Juyao street, Shenzhen, China
Origin Country: China
Device Identifier Type: IMEI
Device Identifier Value: 864456046945278
Certification Numbers: CCC 2023-012345, CE Mark
Price: $599.99
Authenticity Status: Authentic
Category: Electronics
```

**Verification Analysis:**
```
1. Brand Check (Xiaomi → China): ✓ MATCH
   - Xiaomi is a Chinese smartphone manufacturer
   
2. Manufacturer Check:
   - Xiaomi Corporation address in Shenzhen, China ✓ MATCH
   - Shenzhen is a major tech hub
   
3. Device Identifier Check:
   - IMEI prefix "86" typically assigned to China ✓ MATCH
   
4. Certification Check:
   - CCC (China Compulsory Certification) = China ✓
   - CE Mark = EU compliance ✓
   - Both certifications align with China-made product ✓
   
5. Price Check:
   - $599.99 is reasonable for mid-range Chinese smartphone ✓
   - Aligns with Xiaomi's market positioning
   
6. Category Check:
   - Electronics from China is very common ✓
   - Xiaomi is well-known for quality budget electronics ✓
```

**Result:**
```
✓ VALID
Score: 88/100
Confidence: 92%
Reasoning: All verification checks passed. Brand, manufacturer, 
           certifications, and pricing all align with China origin. 
           Product appears legitimate.
Action: Product can go live immediately
```

---

## Example 4: Suspicious "European" Headphones (FAILS 🚩)

**Vendor Input:**
```
Product Name: Premium European Headphones
Brand: Unknown/Generic
Manufacturer: (left blank)
Manufacturer Address: (left blank)
Origin Country: Germany
Device Identifier Type: (none provided)
Certification Numbers: (left blank)
Price: $24.99
Authenticity Status: Unknown
Category: Electronics > Audio
```

**Verification Analysis:**
```
1. Brand Check:
   - No recognized brand provided ✗
   - Generic/Unknown brand is suspicious for "premium" product
   
2. Manufacturer Check:
   - Empty fields ✗
   - No manufacturer information provided
   
3. Certification Check:
   - No certifications provided ✗
   - Audio products should have CE marks at minimum
   - No compliance documentation
   
4. Price Check:
   - $24.99 is very cheap for "European premium headphones" ✗
   - Premium German headphones (Sennheiser, Beyerdynamic) cost $100+
   - This extreme undercut suggests counterfeit
   
5. Authenticity Check:
   - Status is "Unknown" ✗
   - Should be "Authentic" if genuinely European
   
6. Category Check:
   - Electronics from Germany is plausible...
   - But combined with other red flags = suspicious
```

**Detected Flags:**
- Unknown/generic brand (no verification possible)
- No manufacturer or certifications provided
- Extreme price undercut ($24.99 vs $100+ for authentic)
- Missing required compliance documentation

**Result:**
```
🚩 SUSPICIOUS
Score: 22/100
Confidence: 8%
Severity: HIGH

Reasoning: Multiple warning signs suggest counterfeit:
1. Unknown/generic brand - no way to verify
2. No manufacturer information provided
3. Extreme price undercut typical of counterfeits
4. Missing required CE certification
5. No authenticity documentation

Vendor Action Required:
- Provide proof of purchase from authorized supplier
- Provide manufacturer details and certifications
- Justify extreme price undercut
OR
- Request to revise origin to China (actual origin)
- Provide authentic documentation

Admin Recommendation:
- Request documentation before approval
- Consider vendor fraud investigation if patterns continue
```

---

## Example 5: Ambiguous Case - Requires Admin Review (MARGINAL)

**Vendor Input:**
```
Product Name: New Balance Running Shoes
Brand: New Balance
Manufacturer: New Balance Athletics Inc.
Manufacturer Address: Boston, Massachusetts, USA
Origin Country: Vietnam
Device Identifier Type: (not applicable)
Certification Numbers: (not applicable for shoes)
Price: $89.99
Authenticity Status: Authentic
Category: Clothing > Footwear
```

**Verification Analysis:**
```
1. Brand Check (New Balance → US):
   - New Balance is USA-based ✓
   - But New Balance manufactures in multiple countries including Vietnam ⚠️
   - This is actually legitimate (Many US brands use Vietnam manufacturing)
   
2. Manufacturer Check:
   - Manufacturer address is Boston, USA
   - But Origin is Vietnam
   - However, this is common practice for US brands ✓
   
3. Price Check:
   - $89.99 is reasonable for New Balance shoes ✓
   
4. Authenticity:
   - Marked as "Authentic" ✓
```

**Detected Flags:**
- Brand origin (USA) differs from claimed manufacture origin (Vietnam)
- BUT this is legitimate for many US brands

**Result:**
```
⚠️ VALID BUT REQUIRES CLARIFICATION
Score: 68/100
Confidence: 65%
Severity: LOW (Informational)

Reasoning: Origin claim is technically accurate but unusual. 
New Balance is a US brand but manufactures in multiple countries. 
Vietnam origin is legitimate for this brand.

Vendor Recommendation:
- Good to clarify in product description:
  "Made in Vietnam for New Balance (US Company)"

Admin Review: NO - APPROVE
- This is a legitimate case of US brand with overseas manufacturing
- Very common in shoe/apparel industry
- All details check out
```

---

## Example 6: Counterfeit Electronics - High Risk (FAILS 🚩)

**Vendor Input:**
```
Product Name: Authentic Apple iPad Air
Brand: Apple
Manufacturer: (left blank)
Manufacturer Address: "Made in China under license"
Origin Country: US
Device Identifier Type: Serial Number
Device Identifier Value: A1B2C3D4E5F6
Certification Numbers: FCC (unverified)
Price: $199.99
Authenticity Status: Unknown
Category: Electronics
```

**Verification Analysis:**
```
1. Brand Check (Apple → US): ✓ Initially matches
   
2. Manufacturer Check:
   - Says "Made in China under license"
   - Apple doesn't license tablet manufacturing to China ✗
   - Suspicious phrasing ("under license") ✗
   
3. Device Identifier Check:
   - Serial Number "A1B2C3D4E5F6" looks FAKE
   - Apple serial numbers have specific patterns
   - This is too generic/simplistic ✗
   
4. Certification Check:
   - "FCC (unverified)" is suspicious phrasing
   - Real products would show specific FCC ID format ✗
   
5. Price Check:
   - $199.99 for authentic iPad Air is WAY too low ✗
   - Retail price is $600+ minimum
   - This is classic counterfeit pricing ($200 vs $600) ✗
   
6. Authenticity:
   - Status unknown for claimed Apple product ✗
   - Apple products should be marked "Authentic" ✓
```

**Multiple Red Flags:**
- Implausible "made in China under license" claim
- Fake-looking serial number
- Extremely low price ($200 vs $600+)
- Unverified FCC claim
- Unknown authenticity status

**Result:**
```
🚩 CRITICAL - LIKELY COUNTERFEIT
Score: 8/100
Confidence: 2%
Severity: CRITICAL

Reasoning: This appears to be a counterfeit device. Red flags:
1. Implausible manufacturing claim ("under license")
2. Suspicious generic serial number format
3. Extreme price ($199.99 vs $600+ retail) - classic counterfeit indicator
4. Unverified FCC claim
5. Unknown authenticity status

IMMEDIATE ACTION REQUIRED:
- BLOCK product from being listed
- Flag vendor for counterfeit activity
- Potential legal action (counterfeiting)
- Consider permanent vendor suspension
- Report to Apple for trademark infringement

Suggested next steps:
- Contact vendor for proof of authenticity
- Request original retailer documentation
- Verify with Apple directly
```

---

## Summary: How Scores Translate to Action

| Score | Status | Vendor Action | Admin Action |
|-------|--------|---------------|--------------|
| 90-100 | ✓ VALID | Go live | Approve immediately |
| 75-89 | ✓ VALID | Go live | Approve |
| 60-74 | ⚠️ MARGINAL | Can go live* | Review if needed |
| 40-59 | ⚠️ SUSPICIOUS | Requires review | Request documentation |
| 0-39 | 🚩 CRITICAL | Block listing | Investigate vendor |

*"Can go live" means vendor can proceed, but product is marked for enhanced monitoring

---

## Integration Points in Your System

### When Vendor Sees Score 28/100 (Suspicious):
1. JavaScript shows red warning alert
2. Vendor can still save product (not blocking)
3. Product marked as "PENDING_VERIFICATION"
4. Admin notification sent
5. Product doesn't go live until admin approves

### When Vendor Sees Score 92/100 (Valid):
1. Green checkmark displayed
2. Product saves normally
3. Can go live immediately
4. Added to catalog without admin review needed
5. Faster go-to-market for legitimate vendors

---

This system significantly reduces counterfeits while not blocking legitimate vendors with unusual but valid combinations.
