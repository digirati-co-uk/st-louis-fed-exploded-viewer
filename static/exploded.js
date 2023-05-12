let cp;
let cpContainer;
let canvasRow;

if(model.canvas){
    const largeImageWithText = document.getElementById("largeImageWithText");
    const canvasText = document.getElementById("canvasText");
    const largeImageWithoutText = document.getElementById("largeImageWithoutText");
    cpContainer = largeImageWithText || largeImageWithoutText;
    const metadata = document.getElementById("metadata");
    const thumbnails = document.getElementById("thumbnails");
    const canvasImage = document.getElementById("canvasImage");
    canvasRow = document.getElementById("canvasRow");

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
    cp.setAttribute("width", `${cpContainer.clientWidth - 8}`);
    cp.setAttribute("height", `${cpContainer.clientHeight - 4}`);
    cp.setAttribute("manifest-id", model.manifest_id);
    cp.setAttribute("canvas-id", model.canvas.id);
    cpContainer.appendChild(cp);
    canvasImage.remove();
    if(canvasText){
        cp.setAttribute("text-enabled", "true");
        toggleCanvasPanel();
        if(!model.show_text){
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

// I should be able to do this purely with layout! But it's only flexing horizontally
function resize(){
    console.log("resizing");
    const height = document.getElementsByTagName("html")[0].clientHeight;
    const navHeight = document.getElementById("topNav").clientHeight;
    const titleHeight = document.getElementById("titleRow").clientHeight;
    const padding = 30;
    canvasRow.style.height = (height - (navHeight + titleHeight + padding)) + "px";
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