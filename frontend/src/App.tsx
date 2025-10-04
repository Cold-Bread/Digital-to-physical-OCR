import { useState } from "react";
import ControlPanel from "./components/ControlPanel";
import OCROutputs from "./components/OCROutputs";
import { useOCRStore } from "./store/useOCRStore";

function App() {
	const patientList = useOCRStore((s) => s.patientList);
	const clearOCRData = useOCRStore((s) => s.clearOCRData);
	const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

	// Helper function to add a new file to the collection
	const addFile = (file: File) => {
		setSelectedFiles((prev) => {
			// Avoid duplicates based on name and size
			const exists = prev.some(
				(f) => f.name === file.name && f.size === file.size
			);
			if (exists) return prev;
			return [...prev, file];
		});
	};

	// Helper function to clear all files and OCR data
	const clearFiles = () => {
		setSelectedFiles([]);
		clearOCRData();
	};

	return (
		<div className="main-container">
			<OCROutputs boxData={patientList} selectedFiles={selectedFiles} />
			<ControlPanel
				onFileAdd={addFile}
				onFilesClear={clearFiles}
				selectedFiles={selectedFiles}
			/>
		</div>
	);
}

export default App;
