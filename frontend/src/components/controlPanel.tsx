import { usePatientStore } from "../store/globalStore";

function ControlPanel() {
	const { ocrOutput, editableText, setEditableText, resetEditableText } =
		usePatientStore();

	const handleFieldChange = (key: keyof typeof editableText, value: string) => {
		setEditableText({ ...editableText, [key]: value });
	};

	const send = () => {
		// send editableText to backend here
		console.log("Sending patient data:", editableText);
	};

	return (
		<div className="button-Bar">
			<>
				<button id="undo" className="button" onClick={resetEditableText}>
					Undo
				</button>
				<button className="button" onClick={() => console.log("Unused")}>
					Go!
				</button>
				<button id="send" className="button" onClick={send}>
					Send
				</button>
			</>

			<div className="textboxes">
				<div className="text-block">
					<label>Original Text</label>
					<textarea
						className="textbox"
						readOnly
						value={Object.entries(ocrOutput)
							.map(([k, v]) => `${k}: ${v}`)
							.join("\n")}
					/>
				</div>
				<div className="text-block">
					<label>Corrected Text</label>
					<textarea
						className="textbox"
						value={Object.entries(editableText)
							.map(([k, v]) => `${k}: ${v}`)
							.join("\n")}
						onChange={(e) => {
							// Optional: handle bulk changes (if user edits raw text)
						}}
					/>
				</div>
			</div>
		</div>
	);
}

export default ControlPanel;
