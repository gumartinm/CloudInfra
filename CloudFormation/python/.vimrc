" *************************** python-mode ***************************
" for using ftplugin
filetype indent plugin on
" my vim uses python3 :)
let g:pymode_python = 'python3'


" *************************** Save session on quitting Vim ***************************
autocmd VimLeave * NERDTreeClose
autocmd VimLeave * call MakeSession()

"" *************************** Restore session on starting Vim ***************************
"" autocmd VimEnter * call MySessionRestoreFunction()
"autocmd VimEnter * call LoadSession()
autocmd VimEnter * NERDTree
"
"function! MakeSession()
"  let b:sessiondir = $HOME . "/.vim/sessions" . getcwd()
"  if (filewritable(b:sessiondir) != 2)
"    exe 'silent !mkdir -p ' b:sessiondir
"    redraw!
"  endif
"  let b:filename = b:sessiondir . '/session.vim'
"  exe "mksession! " . b:filename
"endfunction
"
"function! LoadSession()
"  let b:sessiondir = $HOME . "/.vim/sessions" . getcwd()
"  let b:sessionfile = b:sessiondir . "/session.vim"
"  if (filereadable(b:sessionfile))
"    exe 'source ' b:sessionfile
"  else
"    echo "No session loaded."
"  endif
"endfunction

map <lt>r :NERDTreeFind<cr>
