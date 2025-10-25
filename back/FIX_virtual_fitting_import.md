# Virtual Fitting Import Fix

## Problem
`clothes.py`에서 `VirtualFitting` 클래스를 임포트하려 했지만, `virtual_fitting.py`에는 `RTMPoseVirtualFitting` 클래스만 정의되어 있었습니다.

## Solution
`clothes.py`의 `get_virtual_fitting()` 함수에서:
- Before: `from virtual_fitting import VirtualFitting`
- After: `from virtual_fitting import RTMPoseVirtualFitting`

## Changes Made
1. Import 구문 수정
2. 인스턴스 생성 시 `device` 파라미터 추가
3. 오류 메시지 개선 (traceback 추가)

## Test
서버 재시작 후 가상 피팅 엔드포인트 테스트 필요:
- POST /api/fit/stream

## Files Modified
- back/routes/clothes.py
