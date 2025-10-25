from itertools import product

# 색상 조화 점수 (더 많은 조합 추가)
COLOR_HARMONY = {
    ("베이지", "네이비"): 20,
    ("베이지", "블랙"): 20,
    ("화이트", "네이비"): 25,
    ("화이트", "블랙"): 30,
    ("베이지", "화이트"): 15,
    ("네이비", "화이트"): 25,
    ("블랙", "화이트"): 30,
    ("블랙", "그레이"): 20,
    ("화이트", "그레이"): 20,
    ("베이지", "브라운"): 15,
    ("블랙", "브라운"): 10,
    ("카키", "베이지"): 15,
    ("카키", "브라운"): 20,
}

# 핏 조화 점수
FIT_HARMONY = {
    ("타이트", "스키니"): 20,
    ("노멀", "노멀"): 20,
    ("루즈", "와이드"): 20,
    ("오버사이즈", "루즈"): 15,
    ("오버사이즈", "와이드"): 25,
    ("타이트", "노멀"): 15,
    ("노멀", "와이드"): 15,
}

# 소재 조화 점수
MATERIAL_HARMONY = {
    ("데님", "데님"): 10,
    ("코튼", "코튼"): 15,
    ("니트", "니트"): 15,
    ("데님", "코튼"): 15,
    ("니트", "코튼"): 12,
}

# 계절 적합도 점수
SEASON_BONUS = {
    ("봄", "봄"): 10,
    ("여름", "여름"): 10,
    ("가을", "가을"): 10,
    ("겨울", "겨울"): 10,
}

# 패턴 조화 점수
PATTERN_HARMONY = {
    ("체크", "스트라이프"): 5,
    ("체크", "솔리드"): 8,
    ("스트라이프", "솔리드"): 8,
    ("도트", "솔리드"): 10,
    ("솔리드", "솔리드"): 3,
}

# 카테고리별 호환성
CATEGORY_COMPATIBILITY = {
    "상의": ["탑", "블라우스", "티셔츠", "니트웨어", "셔츠", "브라탑", "후드티"],
    "하의": ["청바지", "팬츠", "스커트", "레깅스", "조거팬츠"],
    "아우터": ["코트", "재킷", "점퍼", "패딩", "베스트", "가디건", "짚업"],
    "원피스": ["드레스", "점프수트"]
}

# 🎯 최소 점수 기준
MIN_INDIVIDUAL_SCORE = 30.0
MIN_FINAL_SCORE = 70.0

def calculate_individual_score(item, target_style):
    """한 개의 옷이 타겟 스타일과 얼마나 잘 맞는지 점수를 계산"""
    attributes = item.get("attributes", {})
    styles = attributes.get("styles", [])
    
    for style_info in styles:
        if style_info.get("style") == target_style:
            return style_info.get("prob", 0)
    
    return 0

def calculate_color_harmony(top_color, bottom_color):
    """색상 조화도 계산"""
    harmony_score = 0
    
    if not top_color or not bottom_color:
        return 0
    
    # 1. 정확한 색상 페어링
    color_pair = tuple(sorted((top_color, bottom_color)))
    harmony_score += COLOR_HARMONY.get(color_pair, 0)
    
    # 2. 같은 색상 (톤 온 톤) 보너스
    if top_color == bottom_color:
        harmony_score += 8
    
    # 3. 중성색 포함 보너스
    neutral_colors = ["베이지", "블랙", "화이트", "그레이", "네이비", "브라운"]
    if top_color in neutral_colors or bottom_color in neutral_colors:
        harmony_score += 5
    
    # 4. 비슷한 톤 감지 (따뜻한 색 vs 차가운 색)
    warm_colors = ["레드", "오렌지", "옐로우", "핑크", "베이지", "브라운", "카키"]
    cool_colors = ["블루", "그린", "퍼플", "네이비", "화이트", "그레이", "블랙"]
    
    top_is_warm = top_color in warm_colors
    bottom_is_warm = bottom_color in warm_colors
    
    if top_is_warm == bottom_is_warm:  # 같은 톤
        harmony_score += 3
    
    return harmony_score

def calculate_fit_harmony(top_fit, bottom_fit):
    """핏 조화도 계산"""
    harmony_score = 0
    
    if not top_fit or not bottom_fit:
        return 0
    
    # 1. 정확한 핏 매칭
    fit_pair = tuple(sorted((top_fit, bottom_fit)))
    harmony_score += FIT_HARMONY.get(fit_pair, 0)
    
    # 2. 같은 핏 보너스
    if top_fit == bottom_fit:
        harmony_score += 8
    
    # 3. 극단적인 조합 패널티 (너무 극단적)
    extreme_fits = ["오버사이즈"]
    if top_fit in extreme_fits and bottom_fit in extreme_fits:
        harmony_score -= 10
    
    # 4. 밸런스 잡은 조합 보너스
    if (top_fit == "오버사이즈" and bottom_fit == "스키니") or \
       (top_fit == "타이트" and bottom_fit == "루즈"):
        harmony_score += 10
    
    return harmony_score

def calculate_material_harmony(top_material, bottom_material):
    """소재 조화도 계산"""
    harmony_score = 0
    
    if not top_material or not bottom_material:
        return 0
    
    # 1. 정확한 소재 페어링
    material_pair = tuple(sorted((top_material, bottom_material)))
    harmony_score += MATERIAL_HARMONY.get(material_pair, 0)
    
    # 2. 같은 소재 보너스
    if top_material == bottom_material:
        harmony_score += 5
    
    # 3. 계절별 소재 조화
    summer_materials = ["린넨", "코튼", "저지"]
    winter_materials = ["울", "카시미어", "니트", "무스탕"]
    
    if (top_material in summer_materials and bottom_material in summer_materials):
        harmony_score += 5
    elif (top_material in winter_materials and bottom_material in winter_materials):
        harmony_score += 5
    
    return harmony_score

def calculate_detail_harmony(top_details, bottom_details):
    """디테일 조화도 계산"""
    harmony_score = 0
    
    if not top_details or not bottom_details:
        return 0
    
    # 1. 과도한 디테일 방지
    top_detail_count = len(top_details) if isinstance(top_details, list) else 1
    bottom_detail_count = len(bottom_details) if isinstance(bottom_details, list) else 1
    
    if top_detail_count >= 2 and bottom_detail_count >= 2:
        harmony_score -= 5  # 디테일이 너무 많으면 어수선함
    elif top_detail_count == 0 and bottom_detail_count == 0:
        harmony_score += 3  # 심플한 조합
    else:
        harmony_score += 5  # 적절한 디테일 믹스
    
    return harmony_score

def calculate_print_harmony(top_print, bottom_print):
    """프린트 패턴 조화도 계산"""
    harmony_score = 0
    
    if not top_print or not bottom_print:
        return 0
    
    # 1. 정확한 패턴 페어링
    print_pair = tuple(sorted((top_print, bottom_print)))
    harmony_score += PATTERN_HARMONY.get(print_pair, 0)
    
    # 2. 같은 패턴은 피하기
    if top_print == bottom_print and top_print != "솔리드":
        harmony_score -= 8  # 같은 패턴은 어수선함
    
    # 3. 솔리드 + 솔리드 보너스
    if top_print == "솔리드" and bottom_print == "솔리드":
        harmony_score += 5
    
    # 4. 솔리드 + 패턴 조합 보너스
    if (top_print == "솔리드" and bottom_print != "솔리드") or \
       (top_print != "솔리드" and bottom_print == "솔리드"):
        harmony_score += 8
    
    return harmony_score

def calculate_length_harmony(top_length, bottom_length, top_category, bottom_category):
    """기장 조화도 계산"""
    harmony_score = 0
    
    if not top_length or not bottom_length:
        return 0
    
    # 크롭 상의 + 롱 하의 조합 (좋은 조합)
    if top_length == "크롭" and bottom_length in ["미디", "맥시"]:
        harmony_score += 10
    
    # 긴 상의 + 짧은 하의 (좋은 조합)
    if top_length == "롱" and bottom_length == "미니":
        harmony_score += 10
    
    # 노멀한 조합
    if top_length == "노멀" and bottom_length in ["미디", "발목"]:
        harmony_score += 8
    
    return harmony_score

def calculate_season_harmony(top_season, bottom_season):
    """계절 조화도 계산"""
    harmony_score = 0
    
    if not top_season or not bottom_season:
        return 0
    
    # 같은 계절 보너스
    season_pair = (top_season, bottom_season)
    harmony_score += SEASON_BONUS.get(season_pair, 0)
    
    # 계절이 비슷한 경우 보너스
    similar_seasons = {
        "봄": ["여름"],
        "여름": ["봄", "가을"],
        "가을": ["여름", "겨울"],
        "겨울": ["가을"]
    }
    
    if top_season in similar_seasons and bottom_season in similar_seasons[top_season]:
        harmony_score += 3
    
    return harmony_score

def calculate_overall_harmony(top, bottom):
    """전체 조화도 계산 (모든 요소 고려)"""
    top_attrs = top.get("attributes", {})
    bottom_attrs = bottom.get("attributes", {})
    
    harmony_score = 0
    
    # 1. 색상 조화
    top_color = top_attrs.get("color", "")
    bottom_color = bottom_attrs.get("color", "")
    harmony_score += calculate_color_harmony(top_color, bottom_color)
    
    # 2. 핏 조화
    top_fit = top_attrs.get("fit", "")
    bottom_fit = bottom_attrs.get("fit", "")
    harmony_score += calculate_fit_harmony(top_fit, bottom_fit)
    
    # 3. 소재 조화
    top_material = top_attrs.get("material", "")
    bottom_material = bottom_attrs.get("material", "")
    harmony_score += calculate_material_harmony(top_material, bottom_material)
    
    # 4. 디테일 조화
    top_details = top_attrs.get("details", [])
    bottom_details = bottom_attrs.get("details", [])
    harmony_score += calculate_detail_harmony(top_details, bottom_details)
    
    # 5. 프린트 패턴 조화
    top_print = top_attrs.get("print", "솔리드")
    bottom_print = bottom_attrs.get("print", "솔리드")
    harmony_score += calculate_print_harmony(top_print, bottom_print)
    
    # 6. 기장 조화
    top_length = top_attrs.get("length", "노멀")
    bottom_length = bottom_attrs.get("length", "노멀")
    top_category = top.get("sub_category", "")
    bottom_category = bottom.get("sub_category", "")
    harmony_score += calculate_length_harmony(top_length, bottom_length, top_category, bottom_category)
    
    # 7. 계절 조화
    top_season = top_attrs.get("season", "")
    bottom_season = bottom_attrs.get("season", "")
    harmony_score += calculate_season_harmony(top_season, bottom_season)
    
    return harmony_score

def calculate_diversity_bonus(ranked_looks):
    """다양성 보너스 (같은 색상/핏 조합 방지)"""
    for i, look in enumerate(ranked_looks):
        duplicate_penalty = 0
        
        for j, other_look in enumerate(ranked_looks[:i]):
            # 색상이 같으면 페널티
            if (look["top"]["color"] == other_look["top"]["color"] and
                look["bottom"]["color"] == other_look["bottom"]["color"]):
                duplicate_penalty += 5
            
            # 패턴이 같으면 추가 페널티
            if (look["top"]["print"] == other_look["top"]["print"] and
                look["bottom"]["print"] == other_look["bottom"]["print"]):
                duplicate_penalty += 3
        
        look["final_score"] -= duplicate_penalty
    
    return ranked_looks

def recommend_look(wardrobe, target_style):
    """타겟 스타일에 맞는 룩 추천"""
    print(f"\n[recommender_system] '{target_style}' 스타일 추천 시작...")
    print(f"[recommender_system] 최소 개별 점수: {MIN_INDIVIDUAL_SCORE}, 최소 최종 점수: {MIN_FINAL_SCORE}")
    
    # 1. 카테고리별 분류
    candidates = {"상의": [], "하의": []}
    
    for item in wardrobe:
        main_category = item.get("main_category", "")
        
        if main_category not in candidates:
            continue
        
        score = calculate_individual_score(item, target_style)
        
        if score >= MIN_INDIVIDUAL_SCORE:
            item_with_score = item.copy()
            item_with_score['individual_score'] = score
            candidates[main_category].append(item_with_score)
        else:
            print(f"[recommender_system] {item.get('sub_category')} 제외 (점수: {score:.2f} < {MIN_INDIVIDUAL_SCORE})")
    
    # 2. 각 카테고리에서 상위 N개 선정
    top_n = 5
    for category in candidates:
        candidates[category].sort(key=lambda x: x['individual_score'], reverse=True)
        candidates[category] = candidates[category][:top_n]
        print(f"[recommender_system] {category}: {len(candidates[category])}개 선정됨")
    
    # 3. 조합 생성
    if not candidates["상의"] or not candidates["하의"]:
        print(f"[recommender_system] 추천할 상의/하의가 없습니다\n")
        return []
    
    all_combinations = list(product(candidates["상의"], candidates["하의"]))
    print(f"[recommender_system] 총 {len(all_combinations)}개 조합 생성됨")
    
    # 4. 점수 계산 및 랭킹
    ranked_looks = []
    filtered_count = 0
    
    for combo in all_combinations:
        total_style_score = combo[0]['individual_score'] + combo[1]['individual_score']
        harmony_score = calculate_overall_harmony(combo[0], combo[1])
        final_score = total_style_score + harmony_score
        
        if final_score < MIN_FINAL_SCORE:
            filtered_count += 1
            continue
        
        ranked_looks.append({
            "top": {
                "id": combo[0].get('id'),
                "category": combo[0].get('sub_category'),
                "color": combo[0].get('attributes', {}).get('color'),
                "print": combo[0].get('attributes', {}).get('print', '솔리드'),
                "length": combo[0].get('attributes', {}).get('length', '노멀'),
                "score": combo[0]['individual_score']
            },
            "bottom": {
                "id": combo[1].get('id'),
                "category": combo[1].get('sub_category'),
                "color": combo[1].get('attributes', {}).get('color'),
                "print": combo[1].get('attributes', {}).get('print', '솔리드'),
                "length": combo[1].get('attributes', {}).get('length', '노멀'),
                "score": combo[1]['individual_score']
            },
            "final_score": final_score,
            "style_score": total_style_score,
            "harmony_score": harmony_score
        })
    
    # 5. 다양성 보너스 적용
    ranked_looks = calculate_diversity_bonus(ranked_looks)
    
    # 최종 정렬
    ranked_looks.sort(key=lambda x: x['final_score'], reverse=True)
    
    print(f"[recommender_system] 제외된 조합: {filtered_count}개")
    print(f"[recommender_system] {len(ranked_looks)}개 룩 추천 완료\n")
    
    return ranked_looks