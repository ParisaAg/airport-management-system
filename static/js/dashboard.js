document.addEventListener(
"DOMContentLoaded",
()=>{



// ================= FLIGHT CHART =================


const flightCanvas =
document.getElementById("flightChart");



if(flightCanvas){


new Chart(
flightCanvas,
{

type:"doughnut",


data:{


labels:[

"Scheduled",
"Boarding",
"Delayed",
"Cancelled"

],


datasets:[{

data:[

flightData.scheduled,
flightData.boarding,
flightData.delayed,
flightData.cancelled

],


backgroundColor:[

"#0B1F3A",
"#D4AF37",
"#ef4444",
"#64748b"

],


borderWidth:0


}]


},



options:{


responsive:true,


plugins:{


legend:{


position:"bottom"


}


}


}


}

);



}







// ================= OPERATIONS CHART =================


const operationCanvas =
document.getElementById("operationChart");



if(operationCanvas){



new Chart(

operationCanvas,

{


type:"bar",


data:{


labels:[

"Completed",
"In Progress"

],


datasets:[{


label:"Operations",


data:[

operationData.completed,
operationData.in_progress

],


backgroundColor:[

"#D4AF37",
"#0B1F3A"

],


borderRadius:10


}]

},



options:{


responsive:true,


scales:{


y:{


beginAtZero:true


}


},



plugins:{


legend:{


display:false


}


}


}



}


);



}



});