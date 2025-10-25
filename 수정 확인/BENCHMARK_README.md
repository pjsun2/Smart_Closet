# Virtual Fitting Performance Benchmark

가상 피팅 시스템의 성능을 자동으로 측정하고 시각화 보고서를 생성하는 도구입니다.

## 📁 파일 구조

```
back/
├── benchmark_virtual_fitting.py  # 전체 벤치마크 (5-10분 소요)
├── quick_fps_test.py            # 빠른 FPS 테스트 (실시간)
├── run_benchmark.bat            # 벤치마크 실행 스크립트
└── benchmark_results/           # 결과 저장 폴더 (자동 생성)
    ├── {timestamp}_batch_size_benchmark.png
    ├── {timestamp}_inference_interval_benchmark.png
    ├── {timestamp}_inference_scale_benchmark.png
    ├── {timestamp}_comparison_chart.png
    ├── {timestamp}_report.txt
    └── {timestamp}_results.json
```

## 🚀 사용 방법

### 1. 전체 벤치마크 실행 (추천)

**방법 1: 배치 파일 실행**
```bash
run_benchmark.bat
```

**방법 2: 직접 실행**
```bash
cd back
python benchmark_virtual_fitting.py
```

**측정 항목:**
- ✅ Batch Size (1~8)
- ✅ Inference Interval (0.03~0.1s)
- ✅ Inference Scale (30%~100%)

**예상 시간:** 5-10분

**결과물:**
- 📊 4개의 시각화 그래프 (PNG)
- 📄 텍스트 보고서 (TXT)
- 📋 JSON 데이터 (JSON)

---

### 2. 빠른 FPS 테스트 (실시간)

실시간으로 현재 설정의 FPS를 확인하고 싶을 때 사용합니다.

```bash
cd back
python quick_fps_test.py
```

**기능:**
- 🎥 웹캠으로 실시간 FPS 측정
- 📊 화면에 FPS 표시
- ⚙️ 현재 파라미터 확인

**종료:** `q` 키

---

## 📊 벤치마크 결과 예시

### Batch Size Impact
```
Batch Size 1: 25.3 FPS
Batch Size 2: 38.7 FPS
Batch Size 3: 52.1 FPS
Batch Size 4: 64.5 FPS  ⭐ Best
Batch Size 5: 63.2 FPS
Batch Size 6: 61.8 FPS
Batch Size 7: 59.4 FPS
Batch Size 8: 57.1 FPS
```

### Inference Interval Impact
```
0.030s (33.3 FPS): 28.5 FPS
0.040s (25.0 FPS): 32.1 FPS
0.050s (20.0 FPS): 35.8 FPS
0.067s (15.0 FPS): 42.3 FPS  ⭐ Best
0.080s (12.5 FPS): 38.7 FPS
0.100s (10.0 FPS): 33.2 FPS
```

### Inference Scale Impact
```
30%: 72.1 FPS
40%: 68.5 FPS
50%: 62.3 FPS  ⭐ Best (속도/품질 균형)
60%: 54.7 FPS
70%: 45.2 FPS
80%: 38.9 FPS
90%: 32.1 FPS
100%: 25.6 FPS
```

---

## ⚙️ 파라미터 수정하기

### virtual_fitting.py 수정

벤치마크 결과를 바탕으로 최적의 파라미터를 적용하세요.

```python
# back/fit/virtual_fitting.py

# Line 90-95: 추론 간격
self.inference_interval = 0.067  # Best: 0.067s (15 FPS)

# Line 117-119: 배치 크기
self.batch_size = 6  # Best: 4-6

# Line 107: 추론 해상도
self.inference_scale = 0.5  # Best: 0.5 (50%)

# Line 99: 출력 FPS
self.output_fps = 30  # 24-60
```

---

## 📈 성능 최적화 가이드

### 🚀 고속 모드 (속도 우선)
```python
self.inference_interval = 0.05
self.batch_size = 8
self.inference_scale = 0.3
self.output_fps = 60
```
**예상:** ~80 FPS (낮은 품질)

### ⚖️ 균형 모드 (추천)
```python
self.inference_interval = 0.067
self.batch_size = 6
self.inference_scale = 0.5
self.output_fps = 30
```
**예상:** ~60 FPS (좋은 품질)

### 💎 고품질 모드 (품질 우선)
```python
self.inference_interval = 0.1
self.batch_size = 4
self.inference_scale = 0.8
self.output_fps = 24
```
**예상:** ~35 FPS (높은 품질)

---

## 🎯 벤치마크 커스터마이징

### 테스트 범위 변경

`benchmark_virtual_fitting.py` 파일에서 테스트 범위를 수정할 수 있습니다:

```python
# Batch Size 범위 변경 (Line 146)
batch_results = self.benchmark_batch_size([1, 2, 4, 6, 8, 10, 12])

# Inference Interval 범위 변경 (Line 154)
interval_results = self.benchmark_inference_interval([0.02, 0.03, 0.05, 0.08, 0.12])

# Inference Scale 범위 변경 (Line 162)
scale_results = self.benchmark_inference_scale([0.2, 0.4, 0.6, 0.8, 1.0])
```

### 측정 프레임 수 변경

더 정확한 측정을 원하면 프레임 수를 늘리세요:

```python
# Line 147-148
fps = self._measure_fps(vf, num_frames=100)  # 기본: 50
```

---

## 📝 보고서 읽는 법

### 1. PNG 그래프
- **막대 높이**: FPS (높을수록 빠름)
- **막대 위 숫자**: 정확한 FPS 값
- **X축**: 테스트 파라미터
- **Y축**: FPS (Frames Per Second)

### 2. TXT 보고서
- 각 테스트의 상세 결과
- Best Performance: 최고 성능 파라미터

### 3. JSON 데이터
- 프로그래밍으로 분석 가능
- 추가 그래프 생성에 활용

---

## ⚠️ 주의사항

1. **GPU 필수**: CUDA 지원 GPU가 없으면 매우 느림
2. **메모리 여유**: Batch Size가 클수록 VRAM 많이 사용
3. **정확도**: 웹캠 사용 시 실제 성능과 다를 수 있음
4. **백그라운드 종료**: 다른 GPU 사용 프로그램 종료 권장

---

## 🐛 문제 해결

### "CUDA out of memory" 에러
→ Batch Size를 줄이세요 (4 → 2)

### 벤치마크가 너무 느림
→ `num_frames=50`을 `30`으로 줄이세요

### 그래프가 깨져 보임
→ 한글 폰트 설치 또는 영문 제목 사용

---

## 📞 문의

벤치마크 관련 문의나 개선 제안은 이슈로 등록해주세요.

---

**Last Updated:** 2025-10-24
