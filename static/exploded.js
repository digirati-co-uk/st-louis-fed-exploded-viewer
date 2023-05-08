let cp;

if(model.canvas){
    const largeImageWithText = document.getElementById("largeImageWithText");
    const canvasText = document.getElementById("canvasText");
    const largeImageWithoutText = document.getElementById("largeImageWithoutText");
    const metadata = document.getElementById("metadata");
    const thumbnails = document.getElementById("thumbnails");
    const canvasImage = document.getElementById("canvasImage");
    const canvasRow = document.getElementById("canvasRow");

    if(thumbnails){
        thumbnails.style.overflowY = "scroll";
        thumbnails.style.height = "98%";
    }
    if(largeImageWithText){
        largeImageWithText.style.height = "98%";
    }
    if(largeImageWithoutText){
        largeImageWithoutText.style.height = "98%";
    }
    if(metadata){
        metadata.style.overflowY = "scroll";
        metadata.style.height = "98%";
    }

    resize();



    console.log(canvasImage);
    console.log(canvasImage.naturalWidth);
    console.log(canvasImage.naturalHeight);

    const toggleCpTextMode = document.getElementById("toggleCpTextMode");
    toggleCpTextMode.addEventListener("change", () => {
       toggleCanvasPanel(this.checked);
    });

    cp = document.createElement("canvas-panel");
    const initialWidth = (largeImageWithText || largeImageWithoutText).clientWidth;
    const initialHeight = (largeImageWithText || largeImageWithoutText).clientHeight;
    cp.setAttribute("width", initialWidth); // canvasImage.naturalWidth);
    cp.setAttribute("height", initialHeight); //  canvasRow canvasImage.naturalHeight);
    cp.setAttribute("manifest-id", model.manifest_id);
    cp.setAttribute("canvas-id", model.canvas.id);
    cp.setAttribute("text-enabled", "true");

    if(largeImageWithText && canvasText){
        largeImageWithText.appendChild(cp);
        toggleCanvasPanel();
        canvasImage.remove();
        if(model.show_text){

        } else {
            canvasText.remove();
            largeImageWithText.classList.remove("col-md-auto");
            largeImageWithText.classList.add("col-md-6");
            thumbnails.classList.remove("col-md-2");
            thumbnails.classList.add("col-md-3");
            metadata.classList.remove("col-md-2");
            metadata.classList.add("col-md-3");
        }
    }

}

function toggleCanvasPanel(){
    if(document.getElementById("toggleCpTextMode").checked){
        cp.enableTextSelection();
    } else {
        cp.disableTextSelection();
    }
}

// I should be able to do this purely with layout!
function resize(){
    console.log("resizing");
    const height = document.getElementsByTagName("html")[0].clientHeight;
    const navHeight = document.getElementById("topNav").clientHeight;
    const titleHeight = document.getElementById("titleRow").clientHeight;
    const padding = 30;

    canvasRow.style.height = (height - (navHeight + titleHeight + padding)) + "px";
    if(cp){
        // cp.setAttribute("height", canvasRow.style.height - 2);
    }
}

function debounce(func, timeout = 100){
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}

const bounceResize = debounce(() => resize());
window.addEventListener("resize", bounceResize);