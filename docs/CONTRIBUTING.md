# Contributing

If you're missing some feature in afl-utils or like to propose some changes, I'd appreciate
your contributions. Just send your bug reports, feature ideas, code patches or pull requests
either via Github or directly to `hlt99 at blinkenshell dot org`! However before you do so,
please make sure that you've read and understood the rest of this document!

  
## Development branch vs. Stable branch
  
The main development branch is `experimental` whereas `master` only contains stable code and
releases. Changes and new features are committed to the `experimental` branch first. no matter
how small the change is. Developers and early adopters will use the code from `experimental`
during their daily work. Whenever a new feature or code change survived this kind of real world
stress testing for some unspecified amount of time it will be merged into `master` and a new
release is tagged.

**TLDR:** Base your pull requests and patches against the **experimental** branch! If you fail
to do so, I'm going to ask you to do it anyway!

 
## Test driven development
  
afl-utils started out as a little project with just a few Python scripts, that did not much
more what could have been done with some Bash-fu. However we grew bigger and more advanced
features made it into afl-utils. At some point the hacky code became hardly maintainable.
Changing one thing broke three others. In order to prevent this mess a major rewrite was
performed. (Looking at the code today you still may find some hacky left-overs though.) At
the same time **unit testing** was introduced as a means of quality assurance.  

Whenever you change the code run the test suite and make sure nothing breaks. Run
`python setup.py test` to invoke the test suite **before** and **after** you modified parts
of the code. For breaking changes consider updating the affected test in a meaningful way!
If your patch introduces a new feature, please be so kind to
provide appropriate test cases for it! In an ideal world you would write tests first and
use them as the specification for your actual implementation...
  
Using all these external tools testing all aspects of afl-utils is hard. Take a look at
Python's Mocking API. It might save you from a head ache.
 
 **TLDR:** Test your code using the provided test suite and provide unit tests for new
 features! Failing tests and a drop in the test coverage are unacceptable.
 
 
## Python Coding Style

### PEP8

afl-utils follows [PEP8 styling guidelines](https://www.python.org/dev/peps/pep-0008/) to
maximize code readability and maintenance.

To make following PEP8 as painless as possible, I strongly recommend using an Integrated
Development Environment that features PEP8 suggestions, such as
[PyCharm](https://www.jetbrains.com/pycharm/>).

### Indent Style

You may have your own preference, it does not matter because **spaces and tabs do not mix.**

afl-utils uses **spaces** to conform with PEP8 standards. Please use an IDE that can help
you with this.

### Commenting Code

Many coders learned to code without commenting their logic. That works if you are the only
person working on the project, but quickly becomes a problem when it is your job to decipher
what someone else was thinking when coding.

You will probably be relieved to read that code comments are not mandatory, because
[code comments are an apology](http://butunclebob.com/ArticleS.TimOttinger.ApologizeIncode).

Only comment your code if you need to leave a note. (I won't judge you for it.)

### Variable or Option Naming

Whenever you create a variable or configuration option, follow PEP8 standards, they are as
follows:

    Do not make global single-letter variable names, those do not help anybody. Using them
    within a function for a few lines in context is okay, but calling it much later requires
    it be given a proper name.

    Functions are named like ``get_fuzzer_instances()`` and variables are named similarly,
    like ``fuzzer_name``.

### Line Length

To make it simple to review code in a diff viewer (and several other reasons) line length is
limited to 128 characters in Python code.

Python allows plenty of features for one line to be split into multiple lines, those are permitted.
