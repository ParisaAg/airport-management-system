const flightCanvas = document.getElementById(
    'flightChart'
);


if (flightCanvas) {


    new Chart(
        flightCanvas,
        {

            type: 'doughnut',

            data: {

                labels: [
                    'Scheduled',
                    'Boarding',
                    'Delayed',
                    'Cancelled'
                ],


                datasets: [
                    {

                        data: [

                            flightData.scheduled,
                            flightData.boarding,
                            flightData.delayed,
                            flightData.cancelled

                        ]

                    }
                ]

            }

        }
    );

}



const operationCanvas = document.getElementById(
    'operationChart'
);



if(operationCanvas){


    new Chart(

        operationCanvas,

        {

            type:'bar',

            data:{


                labels:[

                    'Completed',
                    'In Progress'

                ],


                datasets:[

                    {

                    data:[

                        operationData.completed,
                        operationData.in_progress

                    ]

                    }

                ]

            }

        }

    );


}