# -*- coding: utf-8 -*-

program =u"""
<meta charset="utf-8">

ISWC 2014 Program (preliminary)
<a href="#session">Sessions</a> |
<a href="#industry">Industry Track</a> |
<a href="#dc">Doctoral Consortium</a>


<h1><a name="session">Sessions</a></h1>
{{#sessions}}
    <h2>{{session_no}}: {{session_name}} ({{paper_count}} talks)</h2>
    {{#paper_all}}

        <div style="padding:10px;margin:10px">

            <div>
                 <span style="font-size:120%;font-weight:bold"> {{title}} </span>
                 <span> {{Track}}</span>
            </div>


            <div style="margin-left:10px;">
                {{author}}
                <br/>
                <br/>
                <b>abstract</b>: <i>{{abstract}}</i>
            </div>
        </div>
    {{/paper_all}}

{{/sessions}}

<hr/>

<h1><a name="industry" >Industry Track</a></h1>
{{#track_Industry}}
    <h2>{{session_time}}: {{session_name}} ({{paper_count}} talks)</h2>
    {{#paper_all}}

        <div style="padding:10px;margin:10px">

            <div>
                 <span style="font-size:120%;font-weight:bold"> {{title}} </span>
            </div>

            <div style="margin-left:10px;">
                {{author}}
            </div>
        </div>
    {{/paper_all}}

{{/track_Industry}}

<hr/>

<h1><a name="dc" >Doctoral Consortium</a></h1>
{{#track_DC}}
        <div style="padding:10px;margin:10px">

            <div>
                 <span style="font-size:120%;font-weight:bold"> {{title}} </span>
            </div>

            <div style="margin-left:10px;">
                {{author}}
                <br/>
                <br/>
                <b>abstract</b>: <i>{{abstract}}</i>
            </div>
        </div>
{{/track_DC}}

"""



program2 =u"""
<meta charset="utf-8">

ISWC 2014 Program (v2)
<a href="#events">Events</a> |
<a href="#dc">Doctoral Consortium</a>


<h1><a name="events">Events</a></h1>
{{#events}}
    <h2>{{start}}-{{end}}
        {{#session_name}}
            {{session_name}} ({{paper_count}} talks)
        {{/session_name}}
        {{^session_name}}
            {{name}}
        {{/session_name}}
    </h2>
    {{#talk_all}}

        <div style="padding:10px;margin:10px">

            <div>
                 <span style="font-size:120%;font-weight:bold"> {{title}} </span>
                 <span> {{Track}}</span>
                 ({{start}}-{{end}})
            </div>


            <div style="margin-left:10px;">
                {{author}}
                {{#abstract}}
                    <br/>
                    <br/>
                    <b>abstract</b>: <i>{{abstract}}</i>
                {{/abstract}}
            </div>
        </div>
    {{/talk_all}}

{{/events}}

<hr/>


<h1><a name="dc" >Doctoral Consortium</a></h1>
{{#track_DC}}
        <div style="padding:10px;margin:10px">

            <div>
                 <span style="font-size:120%;font-weight:bold"> {{title}} </span>
            </div>

            <div style="margin-left:10px;">
                {{author}}
                <br/>
                <br/>
                <b>abstract</b>: <i>{{abstract}}</i>
            </div>
        </div>
{{/track_DC}}

"""



event_tsv =u"""
{{#events}}
{{name}},2014-10-{{day}}T0{{start}}:00,2014-10-{{day}}T0{{end}}:00,,{{location}}
{{/events}}


{{#events}}
{{#talk_all}}
"{{title}}",2014-10-{{day}}T0{{start}}:00,2014-10-{{day}}T0{{end}}:00,,{{location}}
{{/talk_all}}

{{/events}}


{{#track_DC}}
 {{title}}
{{/track_DC}}

"""

people_csv= u"""
{{#people}}
{{Name}},,,,,{{Affiliation}},{{Country}},,{{Role}} ({{Track}})
{{/people}}
"""

paper_csv =u"""
{{#papers}}
{{paper_id}},"{{abstract}}"
{{/papers}}


"""