# (완료·폐기) 대체 디코더 비교 보충절

**2026-08-07 종결.** 이 TODO가 요청한 절은 부록 **S10 (Comparison with alternative decoders)** 으로 작성되었고,
`methods_v2.tex:149`의 `Appendix~A` 오지시도 함께 해소되었다.

⚠️ **이 문서의 §3-1 기각 디코더 목록은 사실과 달랐다.**
`PopVec` / `RidgeEnc` / `GaussML` / `RidgeReg`는 디코더가 아니라 **forward encoding의 readout 변형**이며,
커밋된 수치 산출물이 없다. 실제 비교 대상은 `LDA` / `Ridge` / `KernelRidge` / `SVM` / `MLP` / `ForwardEncoding`이다.

→ 근거와 전체 감사 결과는 **[`DECODER_AUDIT_2026-08-07.md`](DECODER_AUDIT_2026-08-07.md)**.
원본은 `archive/TODO_decoder_comparison.md`.
