if(model.canvas){
    const largeImageWithTextContainer = document.getElementById("largeImageWithText");
    const canvasText = document.getElementById("canvasText");
    const largeImageWithoutTextContainer = document.getElementById("largeImageWithoutText");
    const thumbnails = document.getElementById("thumbnails");
    const canvasImage = document.getElementById("canvasImage");

    const toggleCpTextMode = document.getElementById("toggleCpTextMode");
    toggleCpTextMode.addEventListener("change", () => {
       toggleCanvasPanel(this.checked);
    });

    const cp = document.createElement("canvas-panel");
    cp.setAttribute("manifest-id", model.manifest_id);
    cp.setAttribute("canvas-id", model.canvas.id);
    cp.setAttribute("width", canvasImage.naturalWidth);
    cp.setAttribute("height", canvasImage.naturalHeight);

    if(largeImageWithTextContainer && canvasText){
        largeImageWithTextContainer.appendChild(cp);
        canvasImage.remove();
        if(!model.show_text){
            canvasText.remove();
        }
    }

}

function toggleCanvasPanel(){

}