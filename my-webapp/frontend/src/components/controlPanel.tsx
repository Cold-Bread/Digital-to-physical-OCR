function controlPanel() {
	// Placeholder function for button click handler
	const handleButtonClick = (buttonNumber) => {
		console.log(`Button ${buttonNumber} clicked`);
	};
	const undo = (buttonNumber) => {
		console.log(`Button ${buttonNumber} clicked`);
	};
	return (
		<div className="button-Bar">
			<>
				<button id="undo" className="button" onClick={() => undo(1)}>
					Undo
				</button>
				<button className="button" onClick={() => handleButtonClick(2)}>
					Button 2
				</button>
				<button
					id="send"
					className="button"
					onClick={() => handleButtonClick(3)}
				>
					Send
				</button>
				{/* will be filled with the OCR output that you can edit while looking at
				the images and ai output */}
				<textarea id="editOutput" className="textbox" placeholder="Editiable" />
				{/* static output from the AI, unchangeable by the user */}
				<textarea id="AiOutput" className="textbox" placeholder="Ai output" />
			</>
		</div>
	);
}

export default controlPanel;
