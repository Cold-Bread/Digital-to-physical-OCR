import { useState } from "react";
import { useOCRStore } from "../store/useOCRStore";

const ControlPanel = () => {
	const [jsonPreview, setJsonPreview] = useState({});
	const {
		editableText,
		setEditableText,
		resetAll,
		finalOutput,
		setFinalOutput,
	} = useOCRStore();

	const handleSubmit = async () => {
		if (!editableText.trim()) return;

		try {
			const response = await fetch("http://localhost:8000/add_patient", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ final_data: editableText }),
			});

			if (response.ok) {
				alert("Data submitted successfully!");
				resetAll();
			} else {
				alert("Submission failed.");
			}
		} catch (error) {
			console.error("Submission error:", error);
			alert("Submission error. See console.");
		}
	};

	const simulateLLMOutput = () => {
		const sample = "Name: John Doe\nDOB: 01/01/1970\nLast Visit: 06/15/2024";
		setFinalOutput(sample); // Save the original
		setEditableText(sample); // Set the editable version
	};

	return (
		<div className="control-panel">
			<div className="button-group">
				<button className="button" onClick={simulateLLMOutput}>
					Run Pipeline
				</button>
				<button className="button" onClick={handleSubmit}>
					Submit
				</button>
			</div>

			<div className="textarea-row">
				<textarea
					className="textbox"
					value={editableText}
					onChange={(e) => setEditableText(e.target.value)}
				/>
				<textarea className="textbox" value={finalOutput} readOnly />
			</div>

			<div className="json-preview">
				<pre>{JSON.stringify(jsonPreview, null, 2)}</pre>
			</div>
		</div>
	);
};

export default ControlPanel;
