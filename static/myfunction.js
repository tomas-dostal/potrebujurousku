function myFunction(my_element, result_element) {

    var searched_text = document.getElementById(my_element).value;
    if(searched_text.length > 1) {
        fetch("/api/search?misto=" + searched_text)
            .then(function (response) {
            //$('#dropdown-menu').fadeOut(50);

                return response.json();

            })
            .then(function (myJson) {
                console.log(myJson);
                var i = 0;
                var obj = JSON.parse(myJson);

                // we create an element


                document.getElementById(result_element).innerHTML = "";
                while(i < obj.length)
                {
                    if (obj[i][0] == null && obj[i][2] == null) // jen kraj
                    {
                        var params = '"?kraj_id=replace"'.replace("replace",  obj[i][5]);

                        var button = "<button type='button' class='btn  btn-block btn-dark cut-text'  onclick='redirect(parametry)'><span style='color:lightgray'>kraj_str</span></div></button>";
                        button = button.replace("parametry", params);
                        button = button.replace("kraj_str", obj[i][4]);
                        document.getElementById(result_element).innerHTML += button;

                    } else if (obj[i][0] == null && obj[i][2] != null) // nuts + kraj
                    {
                        var params = '"?nuts3_id=replace"'.replace("replace",  obj[i][2]);

                        var button = "<button type='button' class='btn  btn-block btn-dark cut-text'  onclick='redirect(parametry)'>nuts3_str<span style='color:lightgray'>, kraj_str</span></div></button>";
                        button = button.replace("parametry", params);
                        button = button.replace("nuts3_str", obj[i][3]);
                        button = button.replace("kraj_str", obj[i][4]);
                        document.getElementById(result_element).innerHTML += button;

                    } else if (obj[i][0] != null && obj[i][2] != null) // obecmesto
                    {
                        //         SELECT  null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, nazev_kraj, id_kraj from kraj WHERE nazev_kraj LIKE '%Pra%'

                         var params = '"?obecmesto_id=replace"'.replace("replace",  obj[i][0]);

                        var button = "<button type='button' class='btn  btn-block btn-secondary cut-text'  onclick='redirect(parametry)'>obecmesto_str<span style='color:lightgray'>, kraj_str</span></div></button>";
                        button = button.replace("parametry", params);
                        button = button.replace("obecmesto_str", obj[i][1]);
                        button = button.replace("kraj_str", obj[i][4]);
                        document.getElementById(result_element).innerHTML += button;
                    }
                    i = i + 1;
                }
                if(obj.length == 0) // spapny vstup, neni v databazi
                {
                    document.getElementById(result_element).innerHTML = '<div className="alert alert-danger fade show" role="alert">\n<strong>Nenalezeno!</strong>\nZkuste název napsat znovu. Pokud ani to nepomůže, vyberte místo v okolí. V databázi nejsou obsaženy městské části. </div>'
                }
                //$('#dropdown-menu').hide().fadeIn(50);

                })


            .catch(function (error) {
                console.log("Error: " + error);
            });
    }
}

function redirect(parameters) {

    window.location.href = "/opatreni/" + parameters;

}
