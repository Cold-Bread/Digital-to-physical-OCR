import { useRef, useState } from "react";

const ControlPanel = () => {
	const [boxNumber, setBoxNumber] = useState("");
	const [selectedFile, setSelectedFile] = useState<File | null>(null);
	const fileInputRef = useRef<HTMLInputElement>(null);

	// Placeholder: implement these handlers to update tables in App
	const handleSend = () => {
		// TODO: send boxNumber and file to backend, update tables
		alert(`Send: Box #${boxNumber}, File: ${selectedFile?.name || "none"}`);
	};

	return (
		<div className="control-panel control-panel-bottom">
			<input
				type="text"
				className="box-input"
				placeholder="Box Number"
				value={boxNumber}
				onChange={(e) => setBoxNumber(e.target.value)}
			/>
			<input
				type="file"
				accept="image/*"
				ref={fileInputRef}
				style={{ display: "none" }}
				onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
			/>
			<button className="button" onClick={() => fileInputRef.current?.click()}>
				{selectedFile ? selectedFile.name : "Choose File"}
			</button>
			<button
				className="button"
				onClick={handleSend}
				disabled={!boxNumber || !selectedFile}
			>
				Send
			</button>
		</div>
	);
};

export default ControlPanel;
