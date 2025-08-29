import { useRef, useState } from "react";
import { useOCRStore } from "../store/useOCRStore";

const ControlPanel = () => {
	const [boxNumber, setBoxNumber] = useState("");
	const [selectedFile, setSelectedFile] = useState<File | null>(null);
	const [loading, setLoading] = useState(false);
	const fileInputRef = useRef<HTMLInputElement>(null);
	const setOCRResponse = useOCRStore((s) => s.setOCRResponse);
	const setPatientList = useOCRStore((s) => s.setPatientList);

	const handleSend = async () => {
		if (!boxNumber || !selectedFile) return;
		setLoading(true);
		try {
			// 1. Get patients by box number
			const boxRes = await fetch(`http://localhost:8000/box/${boxNumber}`, {
				method: "POST",
			});
			const patients = await boxRes.json();
			setPatientList(patients);

			// 2. Send image to /process-image
			const formData = new FormData();
			formData.append("file", selectedFile);
			const ocrRes = await fetch("http://localhost:8000/process-image", {
				method: "POST",
				body: formData,
			});
			const ocrData = await ocrRes.json();
			setOCRResponse(ocrData);
		} catch (err) {
			alert("Error processing request. See console.");
			console.error(err);
		}
		setLoading(false);
	};

	return (
		<div className="control-panel control-panel-bottom">
			<input
				type="text"
				className="box-input"
				placeholder="Box Number"
				value={boxNumber}
				onChange={(e) => setBoxNumber(e.target.value)}
				disabled={loading}
			/>
			<input
				type="file"
				accept="image/*"
				ref={fileInputRef}
				style={{ display: "none" }}
				onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
				disabled={loading}
			/>
			<button
				className="button"
				onClick={() => fileInputRef.current?.click()}
				disabled={loading}
			>
				{selectedFile ? selectedFile.name : "Choose File"}
			</button>
			<button
				className="button"
				onClick={handleSend}
				disabled={!boxNumber || !selectedFile || loading}
			>
				{loading ? "Processing..." : "Send"}
			</button>
		</div>
	);
};

export default ControlPanel;
