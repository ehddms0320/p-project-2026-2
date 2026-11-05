# Module integration contract

## Boundary 1: Student → RQ1
Each video frame provides detection boxes, class IDs and confidences plus a timestamp. RQ1 uses unlabeled inference statistics only during deployment. Ground truth may be used to create detector training labels and offline evaluation, never at inference.

## Boundary 2: RQ1 → RQ2
Consecutive drift decisions trigger frame selection only after agreed N-window rule. Selection receives a candidate buffer and budget, returns uniquely identified frames with file names.

## Boundary 3: RQ2 → API
Use multipart upload `POST /v1/adaptation-jobs`; manifest fields are documented in API_SPEC.md. No raw SHIFT dataset or actual ground-truth labels are sent.

## Boundary 4: API → Teacher/Trainer
Not yet connected. Future worker reads validated files, generates teacher pseudo labels, filters by threshold, trains an adapter, writes metadata and SHA256.

## Boundary 5: Adapter → Edge
Not yet connected. Validate compatible Student version, artifact size <=5MB and SHA256 before activation. Save previous adapter for rollback. If split adapter swap is not supported by ONNX runtime, use whole compact model replacement as documented project fallback.

## Evaluation
Use the same fixed sequence/split across A No Adaptation, B Periodic, C TENT/BN Adapt, D Drift + Selection + Cloud. Measure mAP, frame upload count/bytes, detection recall/false alarms, recovery time, and latency.
