const OCRPreview = () => {
	const ocrOutputs = [
		"Detected text from OCR 1...",
		"Detected text from OCR 2...",
		"Detected text from OCR 3...",
	];

	return (
		<div className="ocr-preview">
			{ocrOutputs.map((output, i) => (
				<textarea key={i} className="ocr-textbox" value={output} readOnly />
			))}
		</div>
	);
};

export default OCRPreview;
