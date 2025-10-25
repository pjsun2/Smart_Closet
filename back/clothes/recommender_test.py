from recommender_system import recommend_look
import json

# 🎯 목업 데이터: DB에서 SELECT해온 사용자 옷 데이터
mock_wardrobe = [
    {
        'id': 1,
        'main_category': '상의',
        'sub_category': '티셔츠',
        'attributes': {
            'styles': [
                {'style': '모던', 'prob': 85.5},
                {'style': '캐주얼', 'prob': 10.2},
                {'style': '포멀', 'prob': 4.3}
            ],
            'color': '화이트',
            'fit': '노멀',
            'material': '코튼',
            'print': '솔리드',
            'length': '노멀',
            'details': '없음'
        }
    },
    {
        'id': 2,
        'main_category': '상의',
        'sub_category': '블라우스',
        'attributes': {
            'styles': [
                {'style': '모던', 'prob': 72.3},
                {'style': '로맨틱', 'prob': 20.1},
                {'style': '클래식', 'prob': 7.6}
            ],
            'color': '베이지',
            'fit': '타이트',
            'material': '코튼',
            'print': '솔리드',
            'length': '노멀',
            'details': '단추'
        }
    },
    {
        'id': 3,
        'main_category': '상의',
        'sub_category': '니트웨어',
        'attributes': {
            'styles': [
                {'style': '모던', 'prob': 65.1},
                {'style': '클래식', 'prob': 28.5},
                {'style': '캐주얼', 'prob': 6.4}
            ],
            'color': '검은색',
            'fit': '루즈',
            'material': '니트',
            'print': '솔리드',
            'length': '노멀',
            'details': '없음'
        }
    },
    {
        'id': 4,
        'main_category': '상의',
        'sub_category': '셔츠',
        'attributes': {
            'styles': [
                {'style': '모던', 'prob': 78.9},
                {'style': '클래식', 'prob': 15.2},
                {'style': '캐주얼', 'prob': 5.9}
            ],
            'color': '화이트',
            'fit': '오버사이즈',
            'material': '코튼',
            'print': '스트라이프',
            'length': '노멀',
            'details': '없음'
        }
    },
    {
        'id': 5,
        'main_category': '상의',
        'sub_category': '후드티',
        'attributes': {
            'styles': [
                {'style': '캐주얼', 'prob': 92.1},
                {'style': '모던', 'prob': 5.3},
                {'style': '스포츠', 'prob': 2.6}
            ],
            'color': '그레이',
            'fit': '오버사이즈',
            'material': '코튼',
            'print': '솔리드',
            'length': '노멀',
            'details': '없음'
        }
    },
    {
        'id': 6,
        'main_category': '하의',
        'sub_category': '청바지',
        'attributes': {
            'styles': [
                {'style': '모던', 'prob': 78.9},
                {'style': '캐주얼', 'prob': 18.2},
                {'style': '클래식', 'prob': 2.9}
            ],
            'color': '검은색',
            'fit': '스키니',
            'material': '데님',
            'print': '솔리드',
            'length': '발목',
            'details': '없음'
        }
    },
    {
        'id': 7,
        'main_category': '하의',
        'sub_category': '팬츠',
        'attributes': {
            'styles': [
                {'style': '모던', 'prob': 88.5},
                {'style': '클래식', 'prob': 9.1},
                {'style': '캐주얼', 'prob': 2.4}
            ],
            'color': '베이지',
            'fit': '와이드',
            'material': '코튼',
            'print': '솔리드',
            'length': '발목',
            'details': '없음'
        }
    },
    {
        'id': 8,
        'main_category': '하의',
        'sub_category': '스커트',
        'attributes': {
            'styles': [
                {'style': '로맨틱', 'prob': 85.2},
                {'style': '모던', 'prob': 12.1},
                {'style': '클래식', 'prob': 2.7}
            ],
            'color': '검은색',
            'fit': '노멀',
            'material': '코튼',
            'print': '솔리드',
            'length': '미디',
            'details': '없음'
        }
    },
    {
        'id': 9,
        'main_category': '하의',
        'sub_category': '레깅스',
        'attributes': {
            'styles': [
                {'style': '캐주얼', 'prob': 87.3},
                {'style': '모던', 'prob': 10.2},
                {'style': '스포츠', 'prob': 2.5}
            ],
            'color': '검은색',
            'fit': '타이트',
            'material': '저지',
            'print': '솔리드',
            'length': '발목',
            'details': '없음'
        }
    },
    {
        'id': 10,
        'main_category': '하의',
        'sub_category': '조거팬츠',
        'attributes': {
            'styles': [
                {'style': '캐주얼', 'prob': 91.5},
                {'style': '모던', 'prob': 6.2},
                {'style': '스포츠', 'prob': 2.3}
            ],
            'color': '그레이',
            'fit': '루즈',
            'material': '코튼',
            'print': '솔리드',
            'length': '발목',
            'details': '없음'
        }
    }
]

def test_recommender():
    """추천 알고리즘 테스트"""
    
    print("\n" + "="*80)
    print("🎨 스마트 옷장 추천 시스템 테스트")
    print("="*80)
    
    # 1. 목업 데이터 개요
    print("\n📊 [목업 데이터 개요]")
    print(f"  총 옷 개수: {len(mock_wardrobe)}개")
    
    top_count = len([item for item in mock_wardrobe if item['main_category'] == '상의'])
    bottom_count = len([item for item in mock_wardrobe if item['main_category'] == '하의'])
    
    print(f"  - 상의: {top_count}개")
    print(f"  - 하의: {bottom_count}개")
    
    # 2. 각 옷의 스타일 점수 표시
    print("\n👕 [각 옷의 모던 스타일 점수]")
    for item in mock_wardrobe:
        styles = item['attributes']['styles']
        modern_score = next((s['prob'] for s in styles if s['style'] == '모던'), 0)
        status = "✅" if modern_score >= 30 else "❌"
        print(f"  {status} {item['sub_category']:8} (ID: {item['id']:2}) - 모던 점수: {modern_score:6.2f}점")
    
    # 3. 추천 알고리즘 실행
    print("\n🔄 [추천 알고리즘 실행]")
    print("  대상 스타일: '모던'")
    
    recommendations = recommend_look(mock_wardrobe, '모던')
    
    # 4. 추천 결과 표시
    print("\n✨ [최종 추천 결과]")
    print(f"  추천된 룩: {len(recommendations)}개\n")
    
    if not recommendations:
        print("  추천할 룩이 없습니다.")
        return
    
    # 각 추천 룩 상세 표시
    for rank, look in enumerate(recommendations, 1):
        print(f"  {'─'*76}")
        print(f"  🏆 #{rank} 추천 룩 (최종 점수: {look['final_score']:.2f}점)")
        print(f"  {'─'*76}")
        
        # 상의 정보
        top = look['top']
        print(f"  👔 상의:")
        print(f"     - 카테고리: {top['category']}")
        print(f"     - 색상: {top['color']}")
        print(f"     - 패턴: {top['print']}")
        print(f"     - 기장: {top['length']}")
        print(f"     - 스타일 점수: {top['score']:.2f}점")
        
        # 하의 정보
        bottom = look['bottom']
        print(f"  👖 하의:")
        print(f"     - 카테고리: {bottom['category']}")
        print(f"     - 색상: {bottom['color']}")
        print(f"     - 패턴: {bottom['print']}")
        print(f"     - 기장: {bottom['length']}")
        print(f"     - 스타일 점수: {bottom['score']:.2f}점")
        
        # 점수 분석
        print(f"  📈 점수 분석:")
        print(f"     - 스타일 점수 (상의+하의): {look['style_score']:.2f}점")
        print(f"     - 조화 점수 (색상/핏/소재/패턴/기장/계절): {look['harmony_score']:.2f}점")
        print(f"     - 최종 점수: {look['final_score']:.2f}점")
        print()
    
    # 5. 추천 통계
    print(f"  {'─'*76}")
    print("\n📊 [추천 통계]")
    
    avg_final_score = sum(look['final_score'] for look in recommendations) / len(recommendations)
    avg_harmony_score = sum(look['harmony_score'] for look in recommendations) / len(recommendations)
    
    print(f"  - 평균 최종 점수: {avg_final_score:.2f}점")
    print(f"  - 평균 조화 점수: {avg_harmony_score:.2f}점")
    print(f"  - 최고 점수 룩: {recommendations[0]['final_score']:.2f}점")
    print(f"  - 최저 점수 룩: {recommendations[-1]['final_score']:.2f}점")
    
    # 색상 조합 분석
    color_combinations = [(look['top']['color'], look['bottom']['color']) for look in recommendations]
    print(f"\n  색상 조합:")
    for i, (top_color, bottom_color) in enumerate(color_combinations, 1):
        print(f"    {i}. {top_color} + {bottom_color}")
    
    print("\n" + "="*80 + "\n")
    
    # 6. JSON 형식으로도 반환
    return recommendations

def test_with_different_styles():
    """다른 스타일로도 테스트"""
    print("\n" + "="*80)
    print("🎨 다양한 스타일 테스트")
    print("="*80)
    
    styles = ['모던', '클래식', '캐주얼']
    
    for style in styles:
        print(f"\n\n━━━ '{style}' 스타일 추천 ━━━")
        results = recommend_look(mock_wardrobe, style)
        
        if results:
            print(f"✅ {len(results)}개 룩 추천됨")
            for rank, look in enumerate(results[:3], 1):  # 상위 3개만 표시
                print(f"  {rank}. {look['top']['category']}({look['top']['color']}) + {look['bottom']['category']}({look['bottom']['color']}) - {look['final_score']:.2f}점")
        else:
            print(f"❌ 추천할 룩이 없습니다.")

if __name__ == '__main__':
    # 기본 테스트 실행
    recommendations = test_recommender()
    
    # 다양한 스타일 테스트 (선택)
    # test_with_different_styles()
    
    # JSON 형식으로 저장 (선택)
    # with open('recommendations.json', 'w', encoding='utf-8') as f:
    #     json.dump(recommendations, f, ensure_ascii=False, indent=2)
    # print("✅ 추천 결과를 recommendations.json에 저장했습니다.")