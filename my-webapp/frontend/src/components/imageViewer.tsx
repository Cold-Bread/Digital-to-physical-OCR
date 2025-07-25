function ImageViewer() {
	return (
		<div className="img-container">
			<div className="img-block">
				<h2>Original Image</h2>
				<img
					id="OriginalImage"
					src="https://placehold.co/400x300?text=Placeholder"
					alt="Placeholder"
				/>
			</div>
			<div className="img-block">
				<h2>AI Image</h2>
				<img
					id="AiImage"
					src="https://placehold.co/400x300?text=Placeholder"
					alt="AI Enhanced"
				/>
			</div>
		</div>
	);
}

export default ImageViewer;
