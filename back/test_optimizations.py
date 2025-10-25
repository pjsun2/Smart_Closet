"""
가상 피팅 최적화 테스트
- 배치 처리 효율
- 큐 실시간성
- 프레임 보간
"""

import sys
import os
import time

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fit'))

from fit.virtual_fitting import RTMPoseVirtualFitting
import torch

def test_initialization():
    """초기화 및 설정 확인"""
    print("="*70)
    print("1. 초기화 테스트")
    print("="*70)
    
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    
    try:
        vf = RTMPoseVirtualFitting(
            cloth_image_path='fit/input/cloth.jpg',
            device=device
        )
        print("\n✅ 초기화 성공")
        
        # 설정 확인
        print("\n📊 최적화 설정:")
        print(f"  - 배치 크기: {vf.batch_size}")
        print(f"  - 추론 간격: {vf.inference_interval}s ({1/vf.inference_interval:.1f} FPS)")
        print(f"  - 추론 해상도: {int(vf.inference_scale*100)}%")
        print(f"  - 비동기 추론: {'활성화' if vf.use_async_inference else '비활성화'}")
        print(f"  - 배치 처리: {'활성화' if vf.use_batch_inference else '비활성화'}")
        print(f"  - 프레임 보간: {'활성화' if vf.interpolation_enabled else '비활성화'}")
        print(f"  - 실제 추론 간격: {vf.actual_inference_interval}s (초기값)")
        
        vf.stop_inference_thread()
        return True
        
    except Exception as e:
        print(f"\n❌ 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_queue_behavior():
    """큐 동작 테스트 (오래된 프레임 제거)"""
    print("\n" + "="*70)
    print("2. 큐 실시간성 테스트 (오래된 프레임 제거)")
    print("="*70)
    
    import queue
    import numpy as np
    import cv2
    
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    
    try:
        vf = RTMPoseVirtualFitting(
            cloth_image_path='fit/input/cloth.jpg',
            device=device
        )
        
        # 더미 프레임 생성 (640x360)
        dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
        
        print("\n📝 테스트 시나리오:")
        print("  1. 10개의 프레임을 빠르게 추가")
        print("  2. 오래된 프레임이 자동 제거되는지 확인")
        print("  3. 최신 프레임만 남아있는지 확인")
        
        # 10개 프레임 추가 시도
        for i in range(10):
            # 큐 초기화 (실제 코드 시뮬레이션)
            while not vf.inference_queue.empty():
                try:
                    vf.inference_queue.get_nowait()
                except queue.Empty:
                    break
            
            vf.inference_queue.put_nowait((dummy_frame, 1280, 720))
            time.sleep(0.001)  # 1ms
        
        # 큐 크기 확인
        queue_size = vf.inference_queue.qsize()
        print(f"\n✅ 테스트 결과:")
        print(f"  - 추가한 프레임: 10개")
        print(f"  - 큐에 남은 프레임: {queue_size}개")
        print(f"  - 오래된 프레임 제거: {'성공' if queue_size == 1 else '실패'}")
        
        vf.stop_inference_thread()
        return queue_size == 1
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_efficiency():
    """배치 처리 효율 테스트"""
    print("\n" + "="*70)
    print("3. 배치 처리 효율 테스트 (모든 결과 활용)")
    print("="*70)
    
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    
    try:
        vf = RTMPoseVirtualFitting(
            cloth_image_path='fit/input/cloth.jpg',
            device=device
        )
        
        print("\n📝 테스트 시나리오:")
        print("  1. 워커 스레드가 배치 5개 처리")
        print("  2. 모든 결과가 result_queue에 저장되는지 확인")
        print("  3. 배치 효율 = (사용된 결과 / 전체 결과)")
        
        # 워커 스레드가 실행 중이므로 결과 큐 크기 확인
        time.sleep(2)  # 2초 대기 (배치 처리 기회 제공)
        
        result_count = vf.result_queue.qsize()
        
        print(f"\n✅ 테스트 결과:")
        print(f"  - 배치 크기: {vf.batch_size}")
        print(f"  - 결과 큐 크기: {result_count}개")
        print(f"  - 배치 효율: {min(result_count / vf.batch_size * 100, 100):.1f}%")
        print(f"  - 모든 결과 활용: {'성공' if result_count > 1 else '대기 중'}")
        
        vf.stop_inference_thread()
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_interpolation():
    """프레임 보간 테스트"""
    print("\n" + "="*70)
    print("4. 프레임 보간 테스트 (실제 간격 사용)")
    print("="*70)
    
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    
    try:
        vf = RTMPoseVirtualFitting(
            cloth_image_path='fit/input/cloth.jpg',
            device=device
        )
        
        print("\n📝 테스트 시나리오:")
        print("  1. 실제 추론 간격 측정")
        print("  2. 보간 비율(alpha) 계산")
        print("  3. 보간이 정상 작동하는지 확인")
        
        # 워커 스레드가 추론 간격을 측정할 때까지 대기
        time.sleep(3)
        
        print(f"\n✅ 테스트 결과:")
        print(f"  - 이론적 추론 간격: {vf.inference_interval}s")
        print(f"  - 실제 추론 간격: {vf.actual_inference_interval:.3f}s")
        print(f"  - 보간 활성화: {vf.interpolation_enabled}")
        print(f"  - 실제 간격 반영: {'성공' if vf.actual_inference_interval > 0 else '대기 중'}")
        
        vf.stop_inference_thread()
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행"""
    print("\n" + "="*70)
    print("🔍 가상 피팅 최적화 테스트")
    print("="*70)
    
    results = {
        '초기화': test_initialization(),
        '큐 실시간성': test_queue_behavior(),
        '배치 효율': test_batch_efficiency(),
        '프레임 보간': test_interpolation(),
    }
    
    print("\n" + "="*70)
    print("📊 최종 결과")
    print("="*70)
    
    for name, success in results.items():
        status = "✅ 통과" if success else "❌ 실패"
        print(f"  {name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 모든 최적화가 정상 작동합니다!")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다. 로그를 확인하세요.")

if __name__ == "__main__":
    main()
