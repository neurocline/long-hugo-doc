#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

# To generate the one page documentation:
# $ git clone git@github.com:gohugoio/hugoDocs.git
# $ git clone git@github.com:hamoid/long-hugo-doc.git
# $ long-hugo-doc/generateLongDoc.py --input=hugoDocs/content/ --output=long-hugo-doc/README.md

# Why? I find one long doc easier to navigate (less clicks) and
# it's also searchable within the browser (CTRL+F)

import re, os, argparse

def main():
    parser = argparse.ArgumentParser(description='Generate Hugo documentation in one file')
    parser.add_argument('--input', default="./", help='Input path (.../hugo/docs/content/)')
    parser.add_argument('--output', default="README.md", help='Output file')
    args = parser.parse_args()

    folders = ["about",
               "getting-started",
               "themes",
               "content-management",
               "templates",
               "functions",
               "variables",
               "commands",
               "troubleshooting",
               "tools",
               "hosting-and-deployment",
               "contribute",
               #"maintenance",
               #"news",
               #"readfiles",
               #"release-notes",
               #"showcase",
              ]

    titleRe = re.compile(r'^title\s*: (.*)')
    linktitleRe = re.compile(r'^linktitle\s*: (.*)')
    weightRe = re.compile(r'^weight\s*: ([0-9]+)')
    dividerRe = re.compile(r'^---')
    linksBeforeRe = re.compile(r'\[(.*?)\]\(\/(.*?)\/(.*?)\/?\)', re.S)

    fullDocument = ""
    fullIndex = "# Index\n"

    for folder in folders:
        documents = {}
        index = {}

        fullIndex = fullIndex + "\n## " + folder + "\n\n"
        fullPath = args.input + folder

        if not os.path.isdir(fullPath):
            print("\nFolder \"" + fullPath + "\"" + " not found.\nUse --input to specify the input path.\n")
            quit()

        for mdfile in os.listdir(fullPath):
            mdFilePath = fullPath + "/" + mdfile

            if os.path.isdir(mdFilePath):
              print("\nSkipping directory: " + mdFilePath + "\n");
              continue

            print("Reading " + mdFilePath)

            dividerCount = 0
            title = ""
            linktitle = ""
            weight = 999
            content = ""
            md = open(mdFilePath, 'r', encoding='utf-8')
            inTemplate = 0
            for line in iter(md.readline, ''):
                if dividerCount == 2:
                    line, inTemplate = preprocess(line, inTemplate)
                    content = content + line
                else:
                    m = re.match(titleRe, line)
                    if m: title = m.group(1)

                    m = re.match(linktitleRe, line)
                    if m: linktitle = m.group(1).strip('"')

                    m = re.match(weightRe, line)
                    if m: weight = int(m.group(1))

                    m = re.match(dividerRe, line)
                    if m: dividerCount = dividerCount + 1

            # fix internal links
            content = re.sub(linksBeforeRe, r'[\1](#\2.\3.md)', content)

            # find a unique weight so documents are not overwritten
            found = False
            while not found:
                try:
                    index[weight]
                    weight = weight + 1
                except KeyError:
                    # This is what we're looking for: a weight that's not used yet
                    found = True

            # add title, named anchor, content (indexed by weight)
            documents[weight] = '<a name="%s.%s"></a>\n\n# %s\n\n%s' % (folder, mdfile, title, content)
            index[weight] = '  * <a href="#%s.%s">%s</a>\n' % (folder, mdfile, linktitle or title)

        for key in sorted(documents):
            fullDocument = fullDocument + documents[key]
            fullIndex = fullIndex + index[key]

    f = open(args.output, "w", encoding='utf-8')
    f.write("This is the documentation of [Hugo](http://gohugo.io/) condensed into one long page. I did this to make the documentation easier to search and navigate. This page was automatically generated using a Python script using the documentation available at Hugo's GitHub repository.\n")
    f.write(fullIndex)
    f.write(fullDocument)
    f.close()

# TBD all this quoting breaks if you have template constructs inside backticked or code-fenced
# blocks. Those are already quoted and thus don't need more quoting. Sigh.
# Also, really short things like {{% note %}} should probably just be backticked and not
# code-fenced. The rule is probably "if the whole template is on a single line, backtick it,
# and use code fences for longer constructs.

# Look for template constructs and quote them. This handles both
# arbitrary templates, which are turned into code fences individually, and then
# paired "{{< code ... >}} ... {{< /code >}} blocks, which get turned into
# code fences covering the whole construct. This is still not enough to prevent the
# unified file from turning into garbage eventually, but it helps a lot.
def preprocess(line, inTemplate):

    # If we are not in a template, look for '{{'
    if inTemplate == 0:
        idx = line.find('{{')

        # If we see no {{ characters, we can return the whole line
        # (still not in a template)
        if idx == -1:
            return line, inTemplate

        # We are about to enter a template. Handle {{< code specially, this
        # requires a {{< /code >}} block to exit quoted mode
        if line[idx:idx+8] == "{{< code":
            inTemplate = 2

        # Otherwise, we have text before the template starts,
        # and then text after that we have to process
        else:
            inTemplate = 1

        if idx > 0:
            before = line[:idx] + "\n" + "```\n"
        else:
            before = "```\n"

        after, inTemplate = preprocess(line[idx:], inTemplate)
        return before+after, inTemplate

    # If we are in a template, look for the end of it
    else:
        # If we are in a {{< code ..>}} block, then we don't exit quoted
        # mode until we see the entire {{< /code >}} token
        if inTemplate == 2:
            idx = line.find('{{< /code >}}')
            if idx != -1:
                idx += 13

        # Otherwise, }} is sufficient
        else:
            idx = line.find('}}')
            if idx != -1:
                idx += 2

        # If we see no termination of the template, we can return the whole line
        # (still in the template)
        if idx == -1:
            return line, inTemplate
        inTemplate = 0

        # Close the template and parse the rest of the line,
        # which is no longer in a template
        if idx+1 < len(line):
            before = line[:idx] + "\n" + "```\n"
            after, inTemplate = preprocess(line[idx:], inTemplate)
        else:
            before = line + "```\n"
            after = ""
            inTemplate = 0
 
        return before+after, inTemplate

# -----------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
