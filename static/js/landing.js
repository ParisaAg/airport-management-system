document.addEventListener(
"DOMContentLoaded",
()=>{


// ================= COUNTERS =================


const counters =
document.querySelectorAll(".counter");



counters.forEach(counter=>{


let target =
Number(
counter.dataset.target
);



let current = 0;



let speed =
target / 80;



let update=()=>{


current += speed;



if(current < target){

counter.innerText =
Math.floor(current);

requestAnimationFrame(update);


}else{


counter.innerText =
target;


}


};



update();


});






// ================= SCROLL ANIMATION =================



const elements =
document.querySelectorAll(
".feature-card, .dashboard-window, .network-map, .workflow-line"
);



const observer =
new IntersectionObserver(
(entries)=>{


entries.forEach(entry=>{


if(entry.isIntersecting){


entry.target.classList.add(
"show"
);


}

});

},
{
threshold:.2
}
);

elements.forEach(el=>{

el.classList.add(
"hidden"
);
observer.observe(el);
});

});